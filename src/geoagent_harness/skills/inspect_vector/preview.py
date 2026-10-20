"""Small geometry snapshots from the already inspected frame; no extra I/O."""
import hashlib
import json
import math

MAX_POINTS = 32


def point_preview(frame, layer):
    authority = frame.crs.to_authority() if frame.crs else None
    basis = {'kind': 'wgs84_points', 'layer': str(layer)[:120],
             'total_features': len(frame), 'feature_limit': MAX_POINTS,
             'crs': ':'.join(authority) if authority else None}
    if authority not in {('EPSG', '4326'), ('OGC', 'CRS84')}:
        return {**basis, 'status': 'unavailable',
                'finding': 'Point map requires declared WGS84 longitude/latitude; no reprojection is performed.'}
    points = []
    skipped = 0
    for index, geometry in enumerate(frame.geometry.iloc[:MAX_POINTS]):
        if geometry is None or geometry.is_empty or geometry.geom_type != 'Point':
            skipped += 1
            continue
        x, y = geometry.x, geometry.y
        if not math.isfinite(x) or not math.isfinite(y) or not (-180 <= x <= 180 and -90 <= y <= 90):
            skipped += 1
            continue
        points.append([round(x, 7), round(y, 7), index + 1])
    snapshot = {**basis, 'status': 'available' if points else 'unavailable',
                'points': points, 'examined_features': min(len(frame), MAX_POINTS),
                'skipped_features': skipped, 'truncated': len(frame) > MAX_POINTS,
                'finding': 'First layer only. Non-point, empty and invalid coordinates are omitted; no basemap or reprojection.'}
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return {**snapshot, 'snapshot_sha256': digest}


def geometry_preview(frame, layer):
    """Bounded WGS84 features captured during inspection, never a later file read."""
    from shapely.geometry import mapping
    base = point_preview(frame, layer)
    if base['crs'] not in {'EPSG:4326', 'OGC:CRS84'}:
        return base
    features, vertices, skipped = [], 0, 0
    attributes_truncated = len(frame.columns) - 1 > 12
    columns = [c for c in frame.columns if c != frame.geometry.name][:12]

    def coordinates(value):
        nonlocal vertices
        if isinstance(value, (tuple, list)) and value and isinstance(value[0], (int, float)):
            if len(value) < 2 or not all(math.isfinite(v) for v in value[:2]) or not (-180 <= value[0] <= 180 and -90 <= value[1] <= 90):
                raise ValueError('Invalid coordinate')
            vertices += 1
            if vertices > 2048:
                raise ValueError('Vertex budget')
            return [round(value[0], 7), round(value[1], 7)]
        return [coordinates(child) for child in value]

    for index, (_, row) in enumerate(frame.iloc[:MAX_POINTS].iterrows()):
        geometry = row[frame.geometry.name]
        start = vertices
        if geometry is None or geometry.is_empty or geometry.geom_type not in {'Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon'} or not geometry.is_valid:
            skipped += 1
            continue
        try:
            mapped = mapping(geometry)
            shape = {'type': mapped['type'], 'coordinates': coordinates(mapped['coordinates'])}
            attributes_truncated = attributes_truncated or any(row[key] is not None and len(str(row[key])) > 160 for key in columns)
            properties = {str(key)[:80]: None if row[key] is None else str(row[key])[:160] for key in columns}
            feature = {'type': 'Feature', 'id': index + 1, 'geometry': shape, 'properties': properties}
            if len(json.dumps(features + [feature], allow_nan=False).encode()) > 64000:
                raise ValueError('Byte budget')
            features.append(feature)
        except (ValueError, TypeError, OverflowError):
            vertices = start
            skipped += 1
    snapshot = {**base, 'kind': 'wgs84_geometry', 'status': 'available' if features else 'unavailable',
                'features': features, 'vertices': vertices, 'skipped_features': skipped,
                'attributes_truncated': attributes_truncated,
                'finding': 'First layer only; up to 32 features, 2048 vertices, 12 attributes and 64 KB. Invalid, unsupported or oversized features omitted. No reprojection or basemap.'}
    snapshot.pop('snapshot_sha256', None)
    snapshot['snapshot_sha256'] = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return snapshot


def fit_recorded_geometry(outcome, limit=12000):
    """Retain whole features within the durable per-step projection budget."""
    snapshot = outcome.get('spatial_preview')
    if not isinstance(snapshot, dict) or snapshot.get('kind') != 'wgs84_geometry':
        return outcome
    result = dict(outcome)
    snapshot = dict(snapshot)
    features = list(snapshot.get('features', []))
    snapshot.pop('snapshot_sha256', None)
    result['spatial_preview'] = snapshot
    snapshot['recorded_projection_bytes_limit'] = limit
    # Reserve digest/JSON overhead; do not silently simplify a boundary.
    while features and len(json.dumps(result).encode()) > limit - 300:
        features.pop()
        snapshot['features'] = features
        snapshot['skipped_features'] = snapshot.get('skipped_features', 0) + 1
        snapshot['truncated'] = True
        snapshot['finding'] = 'Recorded geometry projection is bounded to 12 KB; whole features omitted. Inspect durable operation evidence for the larger original snapshot.'
    snapshot['features'] = features
    def vertex_count(value):
        return 1 if isinstance(value, (list, tuple)) and value and isinstance(value[0], (int, float)) else sum(vertex_count(child) for child in value)
    snapshot['vertices'] = sum(vertex_count(feature['geometry']['coordinates']) for feature in features)
    kept = {feature['id'] for feature in features}
    snapshot['points'] = [point for point in snapshot.get('points', []) if point[2] in kept]
    snapshot['status'] = 'available' if features else 'unavailable'
    snapshot['snapshot_sha256'] = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return result
