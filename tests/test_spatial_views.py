"""Spatial view oracles use temporary data, exact values and shared service paths."""
import base64
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from geoagent_harness.interface_api.inspection_policy import bounded_read
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.interface_api.spatial_views import SpatialViewOptions, spatial_result
from geoagent_harness.interface_api.workflow_runs import RunRequest


@pytest.fixture
def root(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    return tmp_path


def source_record(root, path, skill):
    binding=bounded_read(root,action='snapshot',path=path)
    record={'run_id':'f'*32,'plan_sha256':'e'*64,'conversation_id':'c'*32,'status':'completed',
            'steps':[{'step_id':'step_1','skill_id':skill,'status':'completed','arguments':{'path':path},
                      'outcome':{'source_sha256':binding['source_sha256']}}]}
    def query(**options):
        return spatial_result(root,record,RunRequest(action='spatial_view',run_id=record['run_id'],
             confirmed_plan_sha256=record['plan_sha256'],conversation_id=record['conversation_id'],
             step_id='step_1',spatial=SpatialViewOptions(**options)))
    return record,query


def vector_source(root):
    path=root/'data/input/layers.gpkg'
    gpd.GeoDataFrame({'name':['first']},geometry=gpd.points_from_xy([111319.490793],[0]),crs='EPSG:3857').to_file(path,layer='projected',driver='GPKG')
    gpd.GeoDataFrame({'name':['<script>literal</script>']},geometry=gpd.points_from_xy([2],[3]),crs='EPSG:4326').to_file(path,layer='geographic',driver='GPKG')
    return path


def raster_source(root):
    path=root/'data/input/image.tif'
    values=np.array([[[0,10],[20,-9999]],[[100,110],[120,-9999]],[[200,210],[220,-9999]]],dtype='int16')
    with rasterio.open(path,'w',driver='GTiff',width=2,height=2,count=3,dtype='int16',nodata=-9999,crs='EPSG:4326',transform=from_origin(10,20,2,2)) as dataset:
        dataset.write(values)
    return path


def test_vector_layers_display_reprojection_and_exact_identity(root):
    path=vector_source(root);before=path.read_bytes()
    record,query=source_record(root,'data/input/layers.gpkg','inspect_vector')
    value=query(mode='vector')
    assert value['layers']==['projected','geographic']
    assert value['source_crs']=='EPSG:3857' and value['reprojected']
    assert value['spatial_preview']['features'][0]['geometry']['coordinates']==[1,0]
    second=query(mode='vector',layer='geographic')
    assert second['spatial_preview']['features'][0]['properties']['name']=='<script>literal</script>'
    assert not second['reprojected']
    assert value['run_id']==record['run_id'] and value['verified_at_read']
    assert not value['execution_performed'] and not value['approval_performed']
    assert path.read_bytes()==before
    with pytest.raises(InterfaceApiError):query(mode='vector',layer='unknown')


@pytest.mark.parametrize('render,bands',[('gray',[1]),('ramp',[1]),('classes',[1]),('rgb',[1,2,3])])
def test_raster_render_rgba_nodata_and_pixel_values(root,render,bands):
    path=raster_source(root);before=path.read_bytes()
    _,query=source_record(root,'data/input/image.tif','inspect_raster')
    result=query(mode='raster',render=render,bands=bands)
    with MemoryFile(base64.b64decode(result['image'].split(',')[1])) as memory:
        with memory.open() as image:
            assert (image.width,image.height,image.count)==(2,2,4)
            rgba=image.read()
    assert rgba[3,1,1]==0 and rgba[3,0,0]==255
    assert result['nodata_preview_pixels']==1 and result['valid_preview_pixels']==3
    assert result['statistics_scope']=='preview_pixels_only'
    if render=='rgb':assert rgba[:3,0,1].tolist()==[127,127,127]
    if render=='classes':assert len(result['legend'])==3
    pixel=query(mode='pixel',row=0,column=1,bands=bands)
    assert pixel['values']==[float(v) for v in ([10,110,210] if render=='rgb' else [10])]
    assert (pixel['x'],pixel['y'])==(13,19)
    assert query(mode='pixel',row=1,column=1)['values']==[None]
    assert path.read_bytes()==before


def test_changed_source_and_scope_never_yield_fresh_view(root):
    path=raster_source(root)
    record,query=source_record(root,'data/input/image.tif','inspect_raster')
    req=RunRequest(action='spatial_view',run_id=record['run_id'],conversation_id='a'*32,
        confirmed_plan_sha256=record['plan_sha256'],step_id='step_1',spatial=SpatialViewOptions(mode='raster'))
    with pytest.raises(InterfaceApiError,match='exact recorded chat'):spatial_result(root,record,req)
    path.write_bytes(b'changed')
    with pytest.raises(InterfaceApiError):query(mode='raster')
    record['steps'][0]['outcome']={}
    with pytest.raises(InterfaceApiError,match='older result'):query(mode='raster')


def test_raster_bounds_bands_and_control_validation(root):
    raster_source(root);_,query=source_record(root,'data/input/image.tif','inspect_raster')
    with pytest.raises(InterfaceApiError):query(mode='pixel',row=2,column=0)
    with pytest.raises(InterfaceApiError):query(mode='raster',bands=[4])
    with pytest.raises(ValueError):SpatialViewOptions(mode='raster',render='rgb',bands=[1])
    with pytest.raises(ValueError):SpatialViewOptions(mode='vector',layer='a',row=0)
    with pytest.raises(ValueError):SpatialViewOptions(mode='pixel')
    with pytest.raises(ValueError):SpatialViewOptions(mode='raster',path='elsewhere')


def test_preview_size_never_becomes_complete_raster_statistics(root):
    path=root/'data/input/large.tif'
    with rasterio.open(path,'w',driver='GTiff',width=1024,height=512,count=1,dtype='uint8') as dataset:
        dataset.write(np.ones((1,512,1024),dtype='uint8'))
    _,query=source_record(root,'data/input/large.tif','inspect_raster')
    value=query(mode='raster',stretch='percentile')
    assert (value['width'],value['height'])==(256,128)
    assert value['scope']=='nearest_resampled_preview'
    assert value['ranges']==[{'band':1,'minimum':1.,'maximum':1.}]


def test_cli_reads_same_record_without_executing(root):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    raster_source(root)
    record,_=source_record(root,'data/input/image.tif','inspect_raster')
    folder=root/'workflow-state/interface-runs';folder.mkdir(parents=True)
    (folder/(record['run_id']+'.json')).write_text(json.dumps(record))
    payload=root/'view.json';payload.write_text(RunRequest(action='spatial_view',run_id=record['run_id'],conversation_id=record['conversation_id'],confirmed_plan_sha256=record['plan_sha256'],step_id='step_1',spatial=SpatialViewOptions(mode='pixel',row=0,column=0)).model_dump_json())
    result=CliRunner().invoke(app,['workflow-runs','--request-file',str(payload),'--project-root',str(root)])
    assert result.exit_code==0,result.output
    assert json.loads(result.stdout)['values']==[0.]
    assert len(list(folder.glob('*.json')))==1



def test_concurrent_view_budget_refuses_extra_worker_and_releases_slot(root,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import geoagent_harness.interface_api.inspection_policy as policy
    raster_source(root);_,query=source_record(root,'data/input/image.tif','inspect_raster')
    entered,finish=Event(),Event()
    def hold(*args,**kwargs):
        entered.set();assert finish.wait(10);raise InterfaceApiError('fixture read stopped')
    monkeypatch.setattr(policy,'bounded_read',hold)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(query,mode='raster')
        try:
            assert entered.wait(5)
            with pytest.raises(InterfaceApiError,match='Another spatial view'):query(mode='raster')
        finally:finish.set()
        with pytest.raises(InterfaceApiError,match='fixture read stopped'):pending.result()
    with pytest.raises(InterfaceApiError,match='fixture read stopped'):query(mode='raster')



def test_planner_map_context_includes_recorded_raster_without_reading_pixels(root,monkeypatch):
    from geoagent_harness.interface_api.result_exploration import view_context,validate_view
    from geoagent_harness.interface_api.exploration_contracts import ResultViewSpec
    record={'run_id':'f'*32,'plan_sha256':'e'*64,'steps':[{'step_id':'step_1','skill_id':'inspect_raster','status':'completed','outcome':{'width':2,'height':2,'crs':'EPSG:4326'}}]}
    import geoagent_harness.interface_api.run_assessment as assessment
    monkeypatch.setattr(assessment,'latest_conversation_run',lambda *args:record)
    context=view_context(root,'c'*32,object())
    assert context['results'][0]['views']==['Map']
    assert context['results'][0]['spatial_kind']=='raster'
    assert context['results'][0]['recorded_facts']=={'width':2,'height':2,'crs':'EPSG:4326'}
    validate_view(ResultViewSpec(run_id='f'*32,plan_sha256='e'*64,step_id='step_1',view='Map'),context)
    assert not list(root.rglob('*.tif'))



def test_all_nodata_preview_has_no_invented_zero_range(root):
    path=root/'data/input/missing.tif'
    with rasterio.open(path,'w',driver='GTiff',width=2,height=2,count=1,dtype='float32',nodata=-9999,crs='EPSG:4326',transform=from_origin(1,2,1,1)) as dataset:
        dataset.write(np.full((1,2,2),-9999,dtype='float32'))
    _,query=source_record(root,'data/input/missing.tif','inspect_raster')
    value=query(mode='raster',render='ramp')
    assert value['ranges']==[{'band':1,'minimum':None,'maximum':None}]
    assert value['valid_preview_pixels']==0 and value['nodata_preview_pixels']==4
