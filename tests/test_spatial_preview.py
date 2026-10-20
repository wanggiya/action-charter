"""Offline snapshots are bounded, explicit and captured at inspection time."""
import json
import geopandas as gpd
import pytest
from shapely.geometry import Point, LineString
from geoagent_harness.skills.inspect_vector.preview import point_preview
from geoagent_harness.skills.inspect_vector.service import inspect_vector


def test_snapshot_records_known_points_and_digest(tmp_path):
    root=tmp_path/'input';root.mkdir()
    path=root/'points.geojson'
    path.write_text(json.dumps({'type':'FeatureCollection','features':[
        {'type':'Feature','properties':{'label':'<script>alert(1)</script>'},'geometry':{'type':'Point','coordinates':[-71,42]}},
        {'type':'Feature','properties':{},'geometry':{'type':'Point','coordinates':[-70,43]}}
    ]}))
    result=inspect_vector(path,root)
    snapshot=result.spatial_preview
    assert snapshot['status']=='available'
    assert snapshot['crs']=='EPSG:4326'
    assert snapshot['points']==[[-71,42,1],[-70,43,2]]
    assert len(snapshot['snapshot_sha256'])==64
    assert snapshot['features'][0]['properties']['label']=='<script>alert(1)</script>'  # Literal bounded attributes; rendered as text.
    path.unlink()
    assert result.model_dump(mode='json')['spatial_preview']['points']==snapshot['points']


def test_snapshot_bound_skips_invalid_and_nonpoints():
    frame=gpd.GeoDataFrame(geometry=[Point(0,0),Point(181,0),Point(0,91),None,LineString([(0,0),(1,1)])]+[Point(i,0) for i in range(40)],crs='EPSG:4326')
    result=point_preview(frame,'fixture')
    assert result['examined_features']==32 and result['truncated']
    assert result['total_features']==45 and result['skipped_features']==4
    assert len(result['points'])==28
    assert len(json.dumps(result).encode())<3000
    assert all(-180<=point[0]<=180 and -90<=point[1]<=90 for point in result['points'])


@pytest.mark.parametrize('crs',[None,'EPSG:3857'])
def test_unsupported_crs_does_not_invent_reprojection(crs):
    result=point_preview(gpd.GeoDataFrame(geometry=[Point(100000,100000)],crs=crs),'fixture')
    assert result['status']=='unavailable' and 'points' not in result
    assert 'no reprojection' in result['finding']


def test_only_nonpoint_or_empty_data_is_unavailable():
    result=point_preview(gpd.GeoDataFrame(geometry=[None,LineString([(0,0),(1,1)])],crs=4326),'fixture')
    assert result['status']=='unavailable' and result['points']==[]
    assert result['skipped_features']==2


def test_geometry_snapshot_preserves_boundaries_holes_multipart_and_attributes():
    from shapely.geometry import Polygon, MultiPolygon, MultiLineString
    from geoagent_harness.skills.inspect_vector.preview import geometry_preview
    polygon = Polygon([(0,0),(5,0),(5,5),(0,5),(0,0)], holes=[[(1,1),(2,1),(2,2),(1,2),(1,1)]])
    frame = gpd.GeoDataFrame({'name':['boundary','roads','islands']}, geometry=[polygon,MultiLineString([[(0,0),(1,1)],[(3,3),(4,4)]]),MultiPolygon([polygon])],crs=4326)
    result = geometry_preview(frame,'boundaries')
    assert result['status']=='available' and result['kind']=='wgs84_geometry'
    assert len(result['features'])==3 and result['skipped_features']==0
    assert len(result['features'][0]['geometry']['coordinates'])==2
    assert result['features'][1]['geometry']['type']=='MultiLineString'
    assert result['features'][2]['properties']['name']=='islands'
    assert len(result['snapshot_sha256'])==64


def test_geometry_snapshot_vertex_budget_rejects_whole_feature():
    from geoagent_harness.skills.inspect_vector.preview import geometry_preview
    frame=gpd.GeoDataFrame(geometry=[LineString([(i/100,0) for i in range(3000)]),Point(1,1)],crs=4326)
    result=geometry_preview(frame,'fixture')
    assert result['vertices']==1 and result['skipped_features']==1
    assert len(result['features'])==1 and result['features'][0]['id']==2
    assert len(json.dumps(result).encode())<64000


def test_durable_geometry_projection_keeps_whole_features_and_an_explicit_budget():
    from geoagent_harness.skills.inspect_vector.preview import geometry_preview, fit_recorded_geometry
    frame=gpd.GeoDataFrame({f'field_{i}':['x'*120]*25 for i in range(10)},geometry=[Point(i,0) for i in range(25)],crs=4326)
    original=geometry_preview(frame,'fixture')
    assert len(json.dumps(original).encode())>12000
    result=fit_recorded_geometry({'spatial_preview':original})
    snapshot=result['spatial_preview']
    assert 0<len(snapshot['features'])<25 and snapshot['truncated']
    assert len(json.dumps(result).encode())<=12000
    assert len(original['features'])==25  # Original operation evidence unchanged.
    assert snapshot['skipped_features']==25-len(snapshot['features'])
