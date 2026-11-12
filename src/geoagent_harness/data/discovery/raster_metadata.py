"""Bounded TIFF technical metadata; never requests pixel statistics or histograms."""
import json
import math


def technical_metadata(raster):
    import rasterio
    truncated = False
    tag_budget = 1500

    def text(value, limit=160):
        nonlocal truncated
        if value is None:
            return None
        value = str(value)
        if len(value) > limit:
            truncated = True
        return value[:limit]

    def tags(band=0, namespace=None):
        nonlocal tag_budget, truncated
        result = {}
        # Only default and IMAGE_STRUCTURE metadata, never arbitrary subdatasets.
        for key, value in raster.tags(band, ns=namespace).items():
            if len(result) >= 12 or tag_budget <= 0:
                truncated = True
                break
            key, value = text(key, 80), text(value, 200)
            size = len(json.dumps({key: value}).encode())
            if size > tag_budget:
                truncated = True
                continue
            result[key] = value
            tag_budget -= size
        return result

    def number(value):
        return float(value) if value is not None and math.isfinite(value) else None

    dataset_metadata = {'default': tags(), 'IMAGE_STRUCTURE': tags(namespace='IMAGE_STRUCTURE')}
    bands = []
    for index in range(min(raster.count, 16)):
        bands.append({
            'band': index + 1,
            'block_shape': list(raster.block_shapes[index]),
            'color_interpretation': raster.colorinterp[index].name,
            'description': text(raster.descriptions[index], 80),
            'unit': text(raster.units[index], 80),
            'scale': number(raster.scales[index]),
            'offset': number(raster.offsets[index]),
            'overview_levels': raster.overviews(index + 1)[:16],
            'metadata': tags(index + 1),
        })
    overview_dimensions = []
    for level, factor in enumerate(raster.overviews(1)[:16]):
        # Read an overview's header, not an estimated size or resampled pixels.
        with rasterio.open(raster.name, driver='GTiff', overview_level=level) as overview:
            overview_dimensions.append({'factor':factor,'width':overview.width,'height':overview.height})
    result = {
        'schema_version': 'raster-details-v1',
        'crs_wkt': text(raster.crs.to_wkt() if raster.crs else None, 2048),
        'tiled': bool(raster.is_tiled),
        'compression': raster.compression.value if raster.compression else 'NONE',
        'interleave': raster.interleaving.value if raster.interleaving else None,
        'metadata': dataset_metadata,
        'bands': bands,
        'overview_dimensions': overview_dimensions,
        'bands_truncated': raster.count > len(bands),
        'metadata_truncated': truncated,
        'statistics_scope': 'stored_tags_only_not_recomputed',
        'overview_scope': 'first_band_exact_dimensions',
    }
    # Preserve the main inspection even for metadata-heavy TIFFs.
    while len(json.dumps(result).encode()) > 5500 and result['bands']:
        result['bands'].pop()
        result['bands_truncated'] = True
    while len(json.dumps(result).encode()) > 5500 and result['crs_wkt']:
        result['crs_wkt'] = result['crs_wkt'][:len(result['crs_wkt']) // 2]
        result['metadata_truncated'] = True
    return result
