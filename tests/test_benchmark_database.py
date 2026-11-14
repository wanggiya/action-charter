"""Docker lifecycle contract tests use mocks only; never connect to a live service."""
import json
from pathlib import Path

import pytest

from geoagent_harness.apps.benchmark import database as db


@pytest.fixture
def commands(monkeypatch):
    calls=[]
    def docker(*args,**kw):
        calls.append(args)
        if args[:2]==('image','inspect'):return '[{}]'
        if args[0]=='create':return 'a'*64
        if args[0]=='exec':return 'postgres'
        if args[1]=='inspect':
            name=args[-1];identity=name.removeprefix('actioncharter-bench-').removesuffix('-net')
            labels={db.LABEL:identity}
            return json.dumps([{'Config':{'Labels':labels},'Labels':labels}])
        return 'fixture'
    monkeypatch.setattr(db,'_docker',docker)
    import psycopg
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def execute(self,sql):
            assert sql in {'SHOW listen_addresses','CREATE EXTENSION IF NOT EXISTS postgis','CREATE SCHEMA IF NOT EXISTS agent_sandbox'}
            return self
        def fetchone(self):return ('*',)
    def connect(**kwargs):
        assert Path(kwargs['host']).name=='socket' and kwargs['dbname']=='benchmark' and kwargs['user']=='benchmark'
        assert len(kwargs['password'])==48
        return Connection()
    monkeypatch.setattr(psycopg,'connect',connect)
    return calls


def test_disposable_lifecycle_has_no_owner_service_or_persistent_volume(tmp_path,commands):
    with db.DisposableDatabase(tmp_path) as fixture:
        assert Path(fixture.env['POSTGRES_HOST']).name=='socket'
        assert fixture.env['ALLOWED_SCHEMAS']=='agent_sandbox'
        password_path=Path(fixture.env['POSTGRES_PASSWORD_FILE'])
        assert password_path.exists()
    assert not password_path.exists()
    assert fixture.cleanup_complete
    assert json.loads((tmp_path/'database-fixture.json').read_text())['status']=='removed'
    create=next(c for c in commands if c[0]=='create')
    assert '--read-only' in create and '--cap-drop' in create and '--tmpfs' in create
    assert '--rm' in create and '/usr/bin/timeout' in create and '--kill-after=5s' in create
    assert '--publish' not in create and '--privileged' not in create
    assert ('--pull','never')==create[create.index('--pull'):create.index('--pull')+2]
    assert create[create.index('--network')+1]=='none'
    assert not any(c[0]=='network' for c in commands)
    assert any(c[:2]==('container','rm') for c in commands)


def test_label_mismatch_never_removes_an_unowned_container(tmp_path,commands,monkeypatch):
    original=db._docker
    def altered(*args,**kw):
        if args[:2]==('container','inspect'):return json.dumps([{'Config':{'Labels':{db.LABEL:'different-owner'}}}])
        return original(*args,**kw)
    monkeypatch.setattr(db,'_docker',altered)
    with pytest.raises(db.DatabaseFixtureError,match='cleanup'):
        with db.DisposableDatabase(tmp_path):pass
    assert not any(c[:2]==('container','rm') for c in commands)
    assert json.loads((tmp_path/'database-fixture.json').read_text())['status']=='cleanup_required'


def test_missing_image_does_not_create_network_or_container(tmp_path,commands,monkeypatch):
    def missing(*args,**kw):
        commands.append(args)
        raise db.DatabaseFixtureError('Image unavailable')
    monkeypatch.setattr(db,'_docker',missing)
    with pytest.raises(db.DatabaseFixtureError):
        with db.DisposableDatabase(tmp_path):pass
    assert commands==[('image','inspect',db.IMAGE)]
