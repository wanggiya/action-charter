"""Metadata-only spatial discovery, streamed identity and recovery boundaries."""
import hashlib
import json
import os
from pathlib import Path

import pytest
from geoagent_harness.discovery.spatial import inspect,probe,package
from geoagent_harness.interface_api.inspection_policy import bounded_read


@pytest.fixture
def root(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    return tmp_path


def vector(root,extension,count=2):
    import geopandas as gpd
    path=root/'data/input'/('points.'+extension)
    gpd.GeoDataFrame({'id':list(range(count)),'label':['x'*220]*count},
        geometry=gpd.points_from_xy([1]*count,[2]*count),crs='EPSG:4326').to_file(path,
        driver='GPKG' if extension=='gpkg' else 'ESRI Shapefile')
    return path


def raster(root,size=4,bands=1):
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.windows import Window
    path=root/'data/input/terrain.tif'
    with rasterio.open(path,'w',driver='GTiff',width=size,height=size,count=bands,dtype='float32',nodata=-9999,
                       crs='EPSG:4326',transform=from_origin(1,4,.01,.01)) as target:
        for row in range(0,size,64):
            target.write(np.zeros((bands,min(64,size-row),size),dtype='float32'),window=Window(0,row,size,min(64,size-row)))
    return path


def oracle(root,result):
    manifest={}
    for name in result['source_manifest']:
        with (root/name).open('rb') as stream:manifest[name]=hashlib.file_digest(stream,'sha256').hexdigest()
    return hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize('extension',['gpkg','shp'])
def test_vector_metadata_never_materializes_frames(root,extension,monkeypatch):
    import geopandas as gpd
    import pyogrio
    path=vector(root,extension)
    before={p.name:p.read_bytes() for p in path.parent.iterdir()}
    def forbidden(*args,**kwargs):raise AssertionError('Geometry frame materialized')
    monkeypatch.setattr(gpd,'read_file',forbidden);monkeypatch.setattr(pyogrio,'read_dataframe',forbidden)
    phases=[];result=inspect(root,'data/input/'+path.name,on_metadata=phases.append)
    assert phases[0]['discovery']['verification']=='pending' and 'source_sha256' not in phases[0]
    assert result['layers'][0]['feature_count']==2 and result['layers'][0]['crs']=='EPSG:4326'
    assert result['source_sha256']==oracle(root,result)
    assert before=={p.name:p.read_bytes() for p in path.parent.iterdir()}


def test_raster_metadata_never_reads_pixels(root,monkeypatch):
    import rasterio
    path=raster(root)
    original=rasterio.open
    class MetadataOnly:
        def __init__(self,value):self.value=value
        def __enter__(self):return self
        def __exit__(self,*args):self.value.close()
        def __getattr__(self,key):
            if key in {'read','read_masks','statistics','stats','histogram'}:raise AssertionError('Raster pixels read')
            return getattr(self.value,key)
    monkeypatch.setattr(rasterio,'open',lambda *args,**kwargs:MetadataOnly(original(*args,**kwargs)))
    result=inspect(root,'terrain.tif')
    assert result['width']==4 and result['band_count']==1 and result['nodata_values']==[-9999]
    assert result['source_sha256']==oracle(root,result)


@pytest.mark.parametrize('kind',['raster','gpkg','shp'])
def test_large_spatial_worker_hashes_without_original_snapshot_limits(root,kind):
    path=raster(root,2048) if kind=='raster' else vector(root,kind,40000)
    source=bounded_read(root,action='spatial_probe',path='data/input/'+path.name)
    assert source['bytes']>8*1024**2
    seen=[]
    result=bounded_read(root,action='spatial_discover',path=source['path'],source_identity=source['source_identity'],on_metadata=seen.append)
    assert seen and seen[0]['discovery']['verification']=='pending'
    assert result['discovery']['bytes_hashed']==source['bytes']
    assert result['source_sha256']==oracle(root,result)
    if kind!='raster':assert result['layers'][0]['feature_count']==40000
    else:assert result['width']==2048


def test_expensive_counts_and_bounds_are_not_forced_or_invented(root,monkeypatch):
    import pyogrio
    vector(root,'gpkg');original=pyogrio.read_info
    def unavailable(*args,**kwargs):
        assert kwargs['force_feature_count'] is False and kwargs['force_total_bounds'] is False
        value=original(*args,**kwargs);value['features']=-1;value['total_bounds']=None
        return value
    monkeypatch.setattr(pyogrio,'read_info',unavailable)
    result=inspect(root,'points.gpkg')
    assert result['layers'][0]['feature_count'] is None and result['layers'][0]['extent'] is None
    assert result['layers'][0]['feature_count_basis']=='not_computed_expensive'


def test_source_change_and_sidecar_membership_are_bound(root):
    path=vector(root,'shp');source=probe(root,'points.shp')
    path.with_suffix('.prj').write_text('changed')
    with pytest.raises(ValueError,match='changed'):inspect(root,'points.shp',expected_identity=source['source_identity'])
    path.with_suffix('.qix').write_text('unreviewed companion')
    with pytest.raises(ValueError,match='closed'):probe(root,'points.shp')


def test_replacement_during_hash_rejected_and_cancel_never_verifies(root):
    path=raster(root)
    def replace(_):
        new=path.with_suffix('.other');new.write_bytes(path.read_bytes());new.replace(path)
    with pytest.raises(ValueError,match='changed'):inspect(root,'terrain.tif',on_metadata=replace)
    from geoagent_harness.recipes.control import ExecutionCancelled
    def stop():raise ExecutionCancelled('operator stopped')
    with pytest.raises(ExecutionCancelled):inspect(root,'terrain.tif',checkpoint=stop)


def test_symlinks_disguised_inputs_and_journals_rejected(root):
    path=raster(root);link=path.parent/'alias.tif';link.symlink_to(path)
    with pytest.raises(OSError):probe(root,'alias.tif')
    link.unlink();path.write_bytes(b'<VRTDataset/>')
    with pytest.raises(ValueError,match='signature'):probe(root,'terrain.tif')
    path=vector(root,'gpkg');Path(str(path)+'-wal').write_text('active')
    with pytest.raises(ValueError,match='journal'):probe(root,'points.gpkg')


def test_metadata_supports_extra_bands_but_display_bounds_are_separate(root):
    raster(root,bands=17)
    result=inspect(root,'terrain.tif')
    assert result['band_count']==17 and len(result['data_types'])==17


def test_cli_uses_same_spatial_discovery_worker(root):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    raster(root)
    reply=CliRunner().invoke(app,['discover-dataset','terrain.tif','--project-root',str(root)])
    assert reply.exit_code==0,reply.output
    result=json.loads(reply.output)
    assert result['discovery']['verification']=='sha256_complete'
    assert result['source_sha256']==oracle(root,result)


def test_missing_sidecars_wal_mode_and_oversized_sources_fail_closed(root):
    path=vector(root,'shp');path.with_suffix('.shx').unlink()
    with pytest.raises(OSError):probe(root,'points.shp')
    path=vector(root,'gpkg')
    with path.open('r+b') as stream:stream.seek(18);stream.write(b'\x02\x02')
    with pytest.raises(ValueError,match='WAL-mode'):probe(root,'points.gpkg')
    path=raster(root)
    with path.open('r+b') as stream:stream.truncate(1024**3+1)
    with pytest.raises(ValueError,match='1 GiB'):probe(root,'terrain.tif')


def test_nan_nodata_remains_json_safe(root):
    import rasterio
    path=raster(root)
    with rasterio.open(path,'r+') as dataset:dataset.nodata=float('nan')
    result=inspect(root,'terrain.tif')
    assert result['nodata_values']==[None] and result['nodata_encodings']==['NaN']
    json.dumps(result,allow_nan=False)


def test_restart_preserves_incomplete_metadata_without_replaying(root):
    from geoagent_harness.interface_api.workflow_runs import _write,_read
    raster(root)
    partial=probe(root,'terrain.tif')['metadata']
    directory=root/'workflow-state/interface-runs';directory.mkdir(parents=True)
    run_id='a'*32
    record={'run_id':run_id,'status':'running','steps':[
        {'step_id':'step_1','status':'running','arguments':{'path':'data/input/terrain.tif'},'outcome':partial},
        {'step_id':'step_2','status':'queued','arguments':{}}]}
    _write(directory,record)
    restored=_read(directory,run_id)
    assert restored['status']=='interrupted' and restored['failed_step_id']=='step_1'
    assert restored['steps'][0]['outcome']==partial and restored['steps'][1]['status']=='skipped'
    assert 'source_sha256' not in restored['steps'][0]['outcome']
    assert _read(directory,run_id)==restored


def detailed_raster(root):
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling,ColorInterp
    from rasterio.transform import from_origin
    path=root/'data/input/details.tif'
    with rasterio.open(path,'w',driver='GTiff',width=33,height=21,count=1,dtype='int16',
        tiled=True,blockxsize=16,blockysize=16,compress='deflate',nodata=-9999,
        crs='EPSG:4326',transform=from_origin(10,20,.25,.5)) as target:
        target.write(np.ones((1,21,33),dtype='int16'))
        target.scales=(.1,);target.offsets=(2.,);target.units=('metres',)
        target.descriptions=('Elevation <b>literal</b>',);target.colorinterp=(ColorInterp.gray,)
        target.update_tags(owner='Synthetic fixture')
        target.update_tags(1,STATISTICS_MINIMUM='-123',STATISTICS_MAXIMUM='456')
        target.build_overviews([2,4],Resampling.nearest)
    return path


def test_technical_metadata_is_bounded_read_only_and_keeps_stored_stats(root):
    path=detailed_raster(root);before=path.read_bytes()
    result=bounded_read(root,action='spatial_discover',path='data/input/details.tif')
    details=result['technical_details'];band=details['bands'][0]
    assert details['tiled'] and details['compression']=='DEFLATE'
    assert band['block_shape']==[16,16] and band['color_interpretation']=='gray'
    assert (band['unit'],band['scale'],band['offset'])==('metres',.1,2.)
    assert band['metadata']['STATISTICS_MINIMUM']=='-123' # Not recomputed to the actual pixel minimum, 1.
    assert details['statistics_scope']=='stored_tags_only_not_recomputed'
    assert details['overview_dimensions']==[{'factor':2,'width':17,'height':11},{'factor':4,'width':9,'height':6}]
    assert details['metadata']['default']['owner']=='Synthetic fixture'
    assert '4326' in details['crs_wkt']
    assert len(json.dumps(result).encode())<16000 and path.read_bytes()==before
    assert not path.with_suffix('.tif.aux.xml').exists()


def test_metadata_matches_independent_gdalinfo_without_statistics_scan(root):
    import shutil
    import subprocess
    command=shutil.which('gdalinfo')
    if command is None:pytest.skip('Optional independent GDAL CLI oracle is not installed')
    path=detailed_raster(root)
    expected=json.loads(subprocess.check_output([command,'-json',str(path)],timeout=15,
        env={**os.environ,'GDAL_PAM_ENABLED':'NO','PROJ_NETWORK':'OFF'}))
    result=inspect(root,'details.tif');details=result['technical_details'];band=details['bands'][0]
    assert [result['width'],result['height']]==expected['size']
    assert result['driver']==expected['driverShortName']
    a,b,c,d,e,f=result['transform']
    assert [c,a,b,f,d,e]==expected['geoTransform']
    assert band['block_shape']==list(reversed(expected['bands'][0]['block']))
    assert band['scale']==expected['bands'][0]['scale'] and band['offset']==expected['bands'][0]['offset']
    assert band['unit']==expected['bands'][0]['unit']
    assert [[item['width'],item['height']] for item in details['overview_dimensions']]==[item['size'] for item in expected['bands'][0]['overviews']]
    assert details['compression']==expected['metadata']['IMAGE_STRUCTURE']['COMPRESSION']


def test_wide_band_and_tag_metadata_truncates_without_losing_main_result(root):
    import rasterio
    path=raster(root,bands=128)
    with rasterio.open(path,'r+') as target:
        target.update_tags(**{'tag_'+str(i):'x'*1000 for i in range(50)})
    result=bounded_read(root,action='spatial_discover',path='data/input/terrain.tif')
    details=result['technical_details']
    assert result['band_count']==128 and len(result['data_types'])==128
    assert details['bands_truncated'] and details['metadata_truncated']
    assert len(json.dumps(details).encode())<=5500
    assert result['source_sha256']==oracle(root,result)


def test_unicode_wkt_respects_serialized_budget(root):
    import rasterio
    from geoagent_harness.discovery.raster_metadata import technical_metadata
    path=raster(root)
    class CRS:
        def to_wkt(self):return '測'*3000
    class UnicodeCRS:
        crs=CRS()
        def __init__(self,value):self.value=value
        def __getattr__(self,key):return getattr(self.value,key)
    with rasterio.open(path) as source:
        result=technical_metadata(UnicodeCRS(source))
    assert len(json.dumps(result).encode())<=5500
    assert result['metadata_truncated'] and result['bands_truncated']
