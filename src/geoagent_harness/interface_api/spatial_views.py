"""Bounded spatial display reads. No workflow dispatch or client-selected paths."""
from __future__ import annotations
from threading import BoundedSemaphore
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


_VIEW_SLOT = BoundedSemaphore(1)


class SpatialDisplayError(ValueError):
    """Fixed user-facing display finding, never a raw parser diagnostic."""


class SpatialViewOptions(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    mode: Literal['vector', 'raster', 'pixel']
    layer: str | None = Field(default=None, min_length=1, max_length=120)
    bands: list[int] = Field(default_factory=lambda: [1], min_length=1, max_length=3)
    render: Literal['gray', 'ramp', 'rgb', 'classes'] = 'gray'
    stretch: Literal['minmax', 'percentile'] = 'minmax'
    row: int | None = Field(default=None, ge=0, le=100_000_000)
    column: int | None = Field(default=None, ge=0, le=100_000_000)

    @model_validator(mode='after')
    def consistent(self):
        if any(b < 1 or b > 16 for b in self.bands):
            raise ValueError('Choose bands 1 through 16')
        if self.mode == 'pixel':
            if self.row is None or self.column is None:
                raise ValueError('Pixel inspection requires a source row and column')
        elif self.row is not None or self.column is not None:
            raise ValueError('Only pixel inspection accepts row/column')
        if self.mode == 'vector':
            if self.bands != [1] or self.render != 'gray' or self.stretch != 'minmax':
                raise ValueError('Vector views do not accept raster controls')
        elif self.layer is not None:
            raise ValueError('Raster views do not accept vector layers')
        if self.mode == 'raster' and len(self.bands) != (3 if self.render == 'rgb' else 1):
            raise ValueError('RGB requires three bands; other renders require one')
        return self


def spatial_result(root, record, request):
    from .server import InterfaceApiError
    from .inspection_policy import bounded_read
    if (not request.conversation_id or request.conversation_id != record.get('conversation_id')
            or request.confirmed_plan_sha256 != record.get('plan_sha256')):
        raise InterfaceApiError('Spatial view requires the exact recorded chat and plan')
    step = next((s for s in record['steps'] if s['step_id'] == request.step_id), None)
    if not step or step['status'] not in {'completed', 'validated_success', 'reused_completed'}:
        raise InterfaceApiError('Select a completed spatial inspection')
    options = request.spatial
    skill = 'inspect_vector' if options.mode == 'vector' else 'inspect_raster'
    if step['skill_id'] != skill:
        raise InterfaceApiError('The requested view does not match this inspector')
    outcome = step.get('outcome') or {}
    digest = outcome.get('source_sha256') or outcome.get('spatial_source_sha256')
    path = step['arguments'].get('path')
    if not digest or not path:
        raise InterfaceApiError('This older result has no bounded spatial source binding. Its saved snapshot remains available; run a new inspection to enable verified viewing')
    if not _VIEW_SLOT.acquire(blocking=False):
        raise InterfaceApiError('Another spatial view is being prepared; wait for it before requesting a new read')
    try:
        result = bounded_read(root, action='spatial_view', path=path, source_sha256=digest,
                              view_options=options.model_dump(mode='json'))
    finally:
        _VIEW_SLOT.release()
    return {**result, 'run_id': record['run_id'], 'plan_sha256': record['plan_sha256'],
            'conversation_id': record['conversation_id'], 'step_id': step['step_id'],
            'source': path, 'source_sha256': digest, 'verified_at_read': True,
            'execution_performed': False, 'approval_performed': False}


def render_snapshot(path, files, options):
    """Only called inside the existing resource-bounded inspection worker."""
    from pathlib import Path
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix='actioncharter-view-') as directory:
        folder = Path(directory)
        for name, data in files.items():
            (folder / Path(name).name).write_bytes(data)
        local = folder / Path(path).name
        if options.mode == 'vector':
            import geopandas as gpd
            import pyogrio
            from .spatial_inspection_snapshot import MAX_FEATURES, MAX_LAYERS, MAX_FIELDS
            from geoagent_harness.skills.inspect_vector.preview import geometry_preview
            layers = pyogrio.list_layers(local)
            if not 0 < len(layers) <= MAX_LAYERS:
                raise SpatialDisplayError('Vector layer limit exceeded')
            names = [str(item[0]) for item in layers]
            chosen = options.layer or names[0]
            if chosen not in names:
                raise SpatialDisplayError('Choose an existing recorded-source layer')
            info = pyogrio.read_info(local, layer=chosen, force_feature_count=True)
            if not 0 <= info['features'] <= MAX_FEATURES or len(info['fields']) > MAX_FIELDS:
                raise SpatialDisplayError('Vector feature/field limit exceeded')
            frame = gpd.read_file(local, layer=chosen, engine='pyogrio')
            original_crs = frame.crs.to_string() if frame.crs else None
            if frame.crs:
                frame = frame.to_crs('EPSG:4326')
            preview = geometry_preview(frame, chosen, feature_limit=256, vertex_limit=8192, byte_limit=256000)
            return {'kind': 'vector', 'layers': names, 'layer': chosen,
                    'source_crs': original_crs, 'display_crs': 'EPSG:4326' if original_crs else None,
                    'reprojected': original_crs not in (None, 'EPSG:4326', 'OGC:CRS84'),
                    'spatial_preview': preview, 'scope': 'bounded_geometry_sample'}
        return raster_view(local, folder, options)


def _png(rgba):
    import base64
    import struct
    import zlib
    height, width, _ = rgba.shape
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    data = b''.join(b'\x00' + row.tobytes() for row in rgba)
    image = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 6, 0, 0, 0))
    image += chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b'')
    return 'data:image/png;base64,' + base64.b64encode(image).decode()


def raster_view(local, folder, options):
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import Window
    from .spatial_inspection_snapshot import MAX_BANDS, MAX_RASTER_CELLS
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_PAM_ENABLED='NO'):
        with rasterio.open(local, driver='GTiff') as dataset:
            if dataset.count > MAX_BANDS or dataset.width * dataset.height * dataset.count > MAX_RASTER_CELLS:
                raise SpatialDisplayError('Raster dimensions/bands exceed the viewing limit')
            if any(b > dataset.count for b in options.bands):
                raise SpatialDisplayError('Selected band does not exist')
            base = {'kind': options.mode, 'source_width': dataset.width, 'source_height': dataset.height,
                    'band_count': dataset.count, 'crs': dataset.crs.to_string() if dataset.crs else None,
                    'bounds': list(dataset.bounds), 'transform': list(dataset.transform)[:6],
                    'bands': options.bands}
            if options.mode == 'pixel':
                if options.row >= dataset.height or options.column >= dataset.width:
                    raise SpatialDisplayError('Pixel lies outside the source raster')
                values = dataset.read(options.bands, window=Window(options.column, options.row, 1, 1), masked=True)
                x, y = dataset.transform * (options.column + .5, options.row + .5)
                return {**base, 'row': options.row, 'column': options.column, 'x': x, 'y': y,
                        'values': [None if np.ma.is_masked(v) or not np.isfinite(v) else float(v) for v in values[:, 0, 0]],
                        'scope': 'exact_source_pixel'}
            ratio = min(1., 256 / max(dataset.width, dataset.height))
            width, height = max(1, round(dataset.width * ratio)), max(1, round(dataset.height * ratio))
            values = dataset.read(options.bands, out_shape=(len(options.bands), height, width),
                                  masked=True, resampling=Resampling.nearest)
            mask = np.ma.getmaskarray(values) | ~np.isfinite(values.data)
            valid = ~mask.any(axis=0)
            rgba = np.zeros((height, width, 4), dtype=np.uint8)
            ranges = []
            channels = []
            for index, band in enumerate(values):
                finite = band.data[~mask[index]]
                low, high = (0., 0.) if not finite.size else tuple(float(v) for v in (
                    np.percentile(finite, [2, 98]) if options.stretch == 'percentile' else [finite.min(), finite.max()]))
                ranges.append({'band': options.bands[index], 'minimum': low if finite.size else None, 'maximum': high if finite.size else None})
                scaled = np.clip((np.where(mask[index], low, band.data).astype(np.longdouble) - np.longdouble(low)) / (np.longdouble(high) - np.longdouble(low) or 1), 0, 1)
                channels.append(scaled)
            legend = []
            if options.render == 'rgb':
                rgba[:, :, :3] = np.stack(channels, axis=-1) * 255
            elif options.render == 'classes':
                unique = np.unique(values.data[0][valid])
                if len(unique) > 32:
                    raise SpatialDisplayError('Categorical preview exceeds 32 sampled classes; choose a continuous render')
                import hashlib
                for value in unique:
                    color = tuple(65 + b % 160 for b in hashlib.sha256(str(float(value)).encode()).digest()[:3])
                    rgba[valid & (values.data[0] == value), :3] = color
                    legend.append({'value': float(value), 'color': '#%02x%02x%02x' % color})
            elif options.render == 'ramp':
                t = channels[0]
                rgba[:, :, :3] = np.stack([40 + 205 * t, 180 - 90 * t, 225 - 170 * t], axis=-1)
            else:
                rgba[:, :, :3] = np.stack([channels[0]] * 3, axis=-1) * 255
            rgba[:, :, 3] = valid * 255
            return {**base, 'kind': 'raster', 'width': width, 'height': height, 'image': _png(rgba),
                    'render': options.render, 'stretch': options.stretch, 'ranges': ranges, 'legend': legend,
                    'valid_preview_pixels': int(valid.sum()), 'nodata_preview_pixels': int((~valid).sum()),
                    'scope': 'nearest_resampled_preview', 'statistics_scope': 'preview_pixels_only'}
