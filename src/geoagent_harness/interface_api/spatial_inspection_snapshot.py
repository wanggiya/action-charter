"""Closed local spatial inputs for automatic inspection; no model-selected readers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from .inspection_policy import INSPECTION_CONTRACTS

VECTOR = INSPECTION_CONTRACTS['inspect_vector']
RASTER = INSPECTION_CONTRACTS['inspect_raster']
MAX_PACKAGE_BYTES = VECTOR['max_package_bytes']
MAX_FEATURES = VECTOR['max_features']
MAX_LAYERS = VECTOR['max_layers']
MAX_FIELDS = VECTOR['max_fields']
MAX_RASTER_CELLS = RASTER['max_cells']
MAX_BANDS = RASTER['max_bands']


def snapshot(root, path):
    from geoagent_harness.tabular.service import read_bytes
    # Validate the main path with no-follow descriptors before examining siblings.
    main_bytes = read_bytes(root, path)
    source = Path(path)
    suffix = source.suffix.lower()
    paths = [path]
    forbidden = []
    if suffix == '.shp':
        paths = [str(source.with_suffix(ext)) for ext in ('.shp', '.shx', '.dbf')]
        for ext in ('.prj', '.cpg'):
            candidate = source.with_suffix(ext)
            if (root / candidate).exists() or (root / candidate).is_symlink():
                paths.append(str(candidate))
        # A closed package avoids silently dropping uppercase or extra metadata.
        allowed = {Path(name).name for name in paths}
        for sibling in (root / source).parent.iterdir():
            if sibling.name.lower().startswith(source.stem.lower() + '.') and sibling.name not in allowed:
                raise ValueError('Shapefile requires a closed lowercase shp/shx/dbf/prj/cpg package')
    elif suffix == '.gpkg':
        forbidden = [path + ext for ext in ('-wal', '-shm', '-journal')]
    elif suffix in ('.tif', '.tiff'):
        for sibling in (root / source).parent.iterdir():
            if sibling.name.lower().startswith(source.stem.lower() + '.') and sibling.name != source.name:
                raise ValueError('TIFF sidecars or same-stem companion files are not eligible')
        forbidden = [path + ext for ext in ('.aux.xml', '.ovr', '.msk')]
        forbidden += [str(source.with_suffix(ext)) for ext in ('.tfw', '.tifw', '.wld', '.prj')]
    elif suffix != '.geojson':
        raise ValueError('Unsupported spatial inspection source')
    if any((root / name).exists() or (root / name).is_symlink() for name in forbidden):
        raise ValueError('External sidecars or active database journals are not eligible')
    files = {name: main_bytes if name == path else read_bytes(root, name) for name in paths}
    if sum(map(len, files.values())) > MAX_PACKAGE_BYTES:
        raise ValueError('Spatial source package exceeds 32 MiB')
    header = files[path][:16]
    if suffix == '.gpkg' and header != b'SQLite format 3\x00':
        raise ValueError('Expected a GeoPackage SQLite file')
    if suffix in ('.tif', '.tiff') and header[:4] not in (b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+'):
        raise ValueError('Expected an embedded TIFF raster')
    if suffix == '.shp' and header[:4] != b'\x00\x00\x27\x0a':
        raise ValueError('Expected a Shapefile header')
    if suffix == '.geojson':
        content = json.loads(files[path])
        if not isinstance(content, dict) or content.get('type') != 'FeatureCollection':
            raise ValueError('Automatic GeoJSON inspection requires an inline FeatureCollection')
        if not isinstance(content.get('features'), list) or len(content['features']) > MAX_FEATURES:
            raise ValueError('GeoJSON exceeds its feature limit')
        crs = content.get('crs')
        if crs and (not isinstance(crs, dict) or crs.get('type') != 'name'):
            raise ValueError('External GeoJSON CRS links are unsupported')
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return files, digest


def inspect_snapshot(root, path, files):
    """Run existing trusted adapters on a private, finite copy of approved bytes."""
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix='actioncharter-inspection-') as directory:
        folder = Path(directory)
        for name, data in files.items():
            (folder / Path(name).name).write_bytes(data)
        local = folder / Path(path).name
        if local.suffix.lower() in ('.tif', '.tiff'):
            import rasterio
            from geoagent_harness.skills.inspect_raster.schemas import InspectRasterArguments
            from geoagent_harness.skills.inspect_raster.service import inspect_raster
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_PAM_ENABLED='NO'):
                with rasterio.open(local, driver='GTiff') as dataset:
                    if dataset.count > MAX_BANDS or dataset.width * dataset.height * dataset.count > MAX_RASTER_CELLS:
                        raise ValueError('Raster exceeds 16 bands or 100 million band-cells')
                result = inspect_raster(InspectRasterArguments(path=local, input_root=folder)).model_dump(mode='json')
        else:
            import pyogrio
            from geoagent_harness.skills.inspect_vector.service import inspect_vector
            driver = {'.geojson': 'GeoJSON', '.gpkg': 'GPKG', '.shp': 'ESRI Shapefile'}[local.suffix.lower()]
            layers = pyogrio.list_layers(local)
            if not 0 < len(layers) <= MAX_LAYERS:
                raise ValueError('Vector exceeds eight layers or has no layers')
            total = 0
            for name, _ in layers:
                info = pyogrio.read_info(local, layer=str(name), force_feature_count=True)
                if info['features'] < 0:
                    raise ValueError('Unbounded vector feature count')
                total += info['features']
                if info['driver'] != driver or total > MAX_FEATURES or len(info['fields']) > MAX_FIELDS:
                    raise ValueError('Vector driver/feature/field limits exceeded')
            result = inspect_vector(local, input_root=folder).model_dump(mode='json')
        result['source'] = path
        return result
