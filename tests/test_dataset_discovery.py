"""Streaming inspector evidence, resource bounds and shared-service integration."""
import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from geoagent_harness.discovery.csv import inspect, probe
from geoagent_harness.interface_api.inspection_policy import bounded_read


@pytest.fixture
def dataset(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    return tmp_path


def write(root,content,name='orders.csv'):
    path=root/'data/input'/name
    path.write_bytes(content)
    return path


def test_quoted_records_hash_missing_counts_and_pending_metadata(dataset):
    data=b'\xef\xbb\xbfid,note,value\r\n001,"line one\nline two",NA\r\n002,"quote ""inside""",\r\n\r\n'
    path=write(dataset,data)
    phases=[]
    result=inspect(dataset,'orders.csv',on_metadata=lambda value:phases.append(value))
    assert phases[0]['row_count'] is None
    assert 'source_sha256' not in phases[0]
    assert phases[0]['discovery']['verification']=='pending'
    assert result['row_count']==2 and result['missing_counts']=={'id':0,'note':0,'value':1}
    assert result['preview'][0]['note']=='line one\nline two'
    assert result['preview'][0]['value']=='NA' and result['preview'][1]['value'] is None
    assert result['source_sha256']==hashlib.sha256(data).hexdigest()
    assert result['discovery']['bytes_hashed']==path.stat().st_size
    assert result['discovery']['statistics_scope']=='complete_parsed_file'


def test_large_csv_inspection_streams_but_processing_limits_stay(dataset,monkeypatch):
    from geoagent_harness.tabular import service
    path=write(dataset,b'id,note\n')
    row=b'001,'+b'x'*1000+b'\n'
    digest=hashlib.sha256(b'id,note\n')
    with path.open('ab') as stream:
        for _ in range(20000):stream.write(row);digest.update(row)
    def forbidden(*args,**kwargs):raise AssertionError('Full materialization used')
    monkeypatch.setattr(service,'read_frame',forbidden)
    result=service.inspect_csv('orders.csv',SimpleNamespace(project_root=dataset))
    assert result['row_count']==20000 and result['source_sha256']==digest.hexdigest()
    from geoagent_harness.operations.registry import TableMetadata,TableArtifact
    assert TableMetadata.model_validate(result).row_count==20000
    assert TableArtifact.model_json_schema()['properties']['row_count']['maximum']==10000
    assert path.stat().st_size>8*1024**2
    assert len(json.dumps(result).encode())<16000
    with pytest.raises(service.TabularError,match='8 MiB'):service.read_bytes(dataset,'orders.csv')


def test_worker_progress_precedes_complete_hash(dataset):
    data=b'id,note\n'+b'001,hello\n'*11000
    write(dataset,data)
    source=bounded_read(dataset,action='csv_probe',path='data/input/orders.csv')
    seen=[]
    result=bounded_read(dataset,action='csv_discover',path=source['path'],source_identity=source['source_identity'],on_metadata=seen.append)
    assert seen and seen[0]['discovery']['phase']=='verifying'
    assert seen[0]['row_count'] is None
    assert result['row_count']==11000
    assert result['source_sha256']==hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize('content',[b'a,a\n1,2\n',b'a,b\n1,2,3\n',b'a\n'+b'x'*5000+b'\n',b'a\n\xff\n',b'a\n"unfinished\n',b'a\n'+b','*(1024*1024+1)])
def test_invalid_csv_is_not_verified(dataset,content):
    write(dataset,content)
    with pytest.raises((ValueError,UnicodeError,csv.Error)):inspect(dataset,'orders.csv')


def test_mutation_and_replacement_detected_before_accepting_evidence(dataset):
    path=write(dataset,b'a\nx\n')
    source=probe(dataset,'orders.csv')
    path.write_bytes(b'a\ny\n')
    with pytest.raises(ValueError,match='changed'):inspect(dataset,'orders.csv',expected_identity=source['source_identity'])
    def replace(_):
        new=write(dataset,b'a\nz\n',name='replacement.csv');new.replace(path)
    with pytest.raises(ValueError,match='changed'):inspect(dataset,'orders.csv',on_metadata=replace)


def test_safe_open_size_and_cancel(dataset):
    from geoagent_harness.discovery.csv import MAX_BYTES
    from geoagent_harness.recipes.control import ExecutionCancelled
    path=write(dataset,b'a\nx\n')
    (path.parent/'link.csv').symlink_to(path)
    with pytest.raises(ValueError):probe(dataset,'link.csv')
    with pytest.raises(ValueError):probe(dataset,'../orders.csv')
    with path.open('r+b') as stream:stream.truncate(MAX_BYTES+1)
    with pytest.raises(ValueError,match='1 GiB'):probe(dataset,'orders.csv')
    path.write_bytes(b'a\nx\n')
    def stop():raise ExecutionCancelled('operator cancellation')
    with pytest.raises(ExecutionCancelled):inspect(dataset,'orders.csv',checkpoint=stop)


def test_bounded_sampling_does_not_require_reading_complete_input(dataset):
    path=write(dataset,b'a\n'+b'x\n'*200000)
    result=probe(dataset,'orders.csv')
    assert result['metadata']['discovery']['sampled_rows']==20
    assert result['metadata']['row_count'] is None and 'source_sha256' not in result


def test_row_limit_is_processing_only_and_cli_shares_discovery(dataset):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    from geoagent_harness.tabular.service import read_frame,TabularError
    path=write(dataset,b'id\n'+b'001\n'*10001)
    reply=CliRunner().invoke(app,['inspect-csv','orders.csv','--project-root',str(dataset)])
    assert reply.exit_code==0,reply.output
    assert json.loads(reply.output)['row_count']==10001
    with pytest.raises(TabularError,match='row/cell bounds'):read_frame(path.read_bytes())


def test_changes_during_full_scan_are_rejected(dataset,monkeypatch):
    from geoagent_harness.discovery.csv import Reader
    path=write(dataset,b'id,note\n'+b'001,hello\n'*20000)
    original=Reader.readinto
    changed=False
    def mutate(self,buffer):
        nonlocal changed
        length=original(self,buffer)
        if self.limit>256*1024 and not changed:
            changed=True
            with path.open('r+b') as stream:stream.seek(10);stream.write(b'z')
        return length
    monkeypatch.setattr(Reader,'readinto',mutate)
    with pytest.raises(ValueError,match='changed'):inspect(dataset,'orders.csv')


def test_deadline_failure_is_not_complete_evidence(dataset,monkeypatch):
    import geoagent_harness.discovery.csv as service
    write(dataset,b'a\nx\n')
    times=iter([0,121])
    monkeypatch.setattr(service.time,'monotonic',lambda:next(times))
    with pytest.raises(ValueError,match='120-second'):probe(dataset,'orders.csv')


def test_worker_cancellation_after_metadata_reaps_child(dataset,monkeypatch):
    import geoagent_harness.interface_api.inspection_policy as policy
    from geoagent_harness.recipes.control import ExecutionCancelled
    write(dataset,b'a\n'+b'x\n'*100000)
    original=policy.subprocess.Popen
    children=[]
    def track(*args,**kwargs):
        child=original(*args,**kwargs);children.append(child);return child
    monkeypatch.setattr(policy.subprocess,'Popen',track)
    def stop(_):raise ExecutionCancelled('operator cancellation')
    with pytest.raises(ExecutionCancelled):bounded_read(dataset,action='csv_discover',path='data/input/orders.csv',on_metadata=stop)
    assert children and all(child.poll() is not None for child in children)
