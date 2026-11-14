"""Opt-in disposable database fixture. Never accepts an existing service address."""
from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4

IMAGE='postgis/postgis:16-3.4'
LABEL='actioncharter.benchmark.fixture'


class DatabaseFixtureError(RuntimeError):
    pass


def _docker(*args, timeout=30, missing_ok=False):
    try:
        result=subprocess.run(['docker',*args],capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        raise DatabaseFixtureError('Disposable database Docker command unavailable') from None
    if result.returncode and missing_ok and args[-1] in result.stderr and ('no such' in result.stderr.lower() or 'not found' in result.stderr.lower()):return ''
    if result.returncode:
        raise DatabaseFixtureError('Disposable database Docker command failed')
    return result.stdout.strip()


class DisposableDatabase(AbstractContextManager):
    def __init__(self, directory, *, lifetime=180):
        if type(lifetime) not in {int,float} or not 1<=lifetime<=86460:raise ValueError('Invalid disposable fixture lifetime')
        self.lifetime=float(lifetime)
        self.directory=Path(directory)
        self.identity=uuid4().hex
        self.name='actioncharter-bench-'+self.identity
        self.temporary=None;self.env=None;self.cleanup_complete=False
        self.container_attempted=False

    def __enter__(self):
        try:
            _docker('image','inspect',IMAGE)  # no pull or package installation
            self.temporary=tempfile.TemporaryDirectory(prefix='actioncharter-bench-credential-')
            password=secrets.token_hex(24)
            secret=Path(self.temporary.name)/'password'
            socket_directory=Path(self.temporary.name)/'socket';socket_directory.mkdir(mode=0o777);socket_directory.chmod(0o777)
            secret.write_text(password);secret.chmod(0o644)  # parent is 0700; container postgres must read bind
            self.container_attempted=True
            identifier=_docker('create','--rm','--name',self.name,'--label',LABEL+'='+self.identity,
                '--pull','never','--network','none',
                '--read-only','--user','postgres','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--memory','512m','--cpus','1','--shm-size','64m',
                '--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=256m,mode=1777',
                '--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
                '--mount',f'type=bind,source={socket_directory},target=/var/run/postgresql',
                '--mount',f'type=bind,source={secret},target=/run/benchmark-password,readonly',
                '--env','POSTGRES_PASSWORD_FILE=/run/benchmark-password',
                '--env','PGDATA=/var/lib/postgresql/data/pgdata','--env','POSTGRES_USER=benchmark',
                '--env','POSTGRES_DB=benchmark','--entrypoint','/usr/bin/timeout',IMAGE,
                '--signal=TERM','--kill-after=5s',str(self.lifetime),'/usr/local/bin/docker-entrypoint.sh','postgres')
            if not re.fullmatch('[a-f0-9]{64}',identifier):raise DatabaseFixtureError('Unexpected container identity')
            self._record({'container':self.name,'fixture_id':self.identity,'status':'created'})
            _docker('start',self.name)
            # Only this new private directory is mounted into this owned container.
            # No TCP listener is reachable: container networking is disabled.
            host=str(socket_directory)
            self.env={'POSTGRES_HOST':host,'POSTGRES_PORT':'5432','POSTGRES_DB':'benchmark',
                'POSTGRES_USER':'benchmark','POSTGRES_PASSWORD_FILE':str(secret),'ALLOWED_SCHEMAS':'agent_sandbox'}
            import psycopg
            deadline=time.monotonic()+45
            while True:
                try:
                    if time.monotonic()>deadline:raise DatabaseFixtureError('Database fixture readiness failed')
                    with psycopg.connect(host=host,port=5432,dbname='benchmark',
                            user='benchmark',password=password,connect_timeout=1) as connection:
                        # The entrypoint's temporary initdb server disables TCP listening.
                        if connection.execute('SHOW listen_addresses').fetchone()[0]=='':
                            time.sleep(.2);continue
                        connection.execute('CREATE EXTENSION IF NOT EXISTS postgis')
                        connection.execute('CREATE SCHEMA IF NOT EXISTS agent_sandbox')
                    break
                except psycopg.Error:
                    if time.monotonic()>deadline:raise DatabaseFixtureError('Database fixture readiness failed') from None
                    time.sleep(.2)
            self._record({'container':self.name,'fixture_id':self.identity,'status':'ready'})
            return self
        except BaseException:
            self.__exit__(None,None,None)
            raise

    def _record(self,value):
        from geoagent_harness.platform.storage.files import FileJsonRecords
        FileJsonRecords(self.directory,max_bytes=4096).replace('database-fixture.json',json.dumps(value))

    def __exit__(self,*_):
        # Check exact ownership labels before touching anything, including failed startup.
        errors=[]
        for kind,name,attempted in (('container',self.name,self.container_attempted),):
            if not attempted:continue
            try:
                raw=_docker(kind,'inspect',name,missing_ok=True)
                if not raw:continue
            except DatabaseFixtureError:
                errors.append('cleanup_unconfirmed');continue
            record=json.loads(raw)[0]
            labels=record.get('Config',{}).get('Labels',{}) if kind=='container' else record.get('Labels',{})
            if labels.get(LABEL)!=self.identity:
                errors.append('ownership_mismatch');continue
            try:
                _docker(kind,'rm',*(['--force'] if kind=='container' else []),name)
            except DatabaseFixtureError:errors.append('cleanup_failed')
        self.cleanup_complete=not errors
        if self.temporary:self.temporary.cleanup()
        self._record({'container':self.name,'fixture_id':self.identity,
            'status':'removed' if self.cleanup_complete else 'cleanup_required'})
        if errors and _[0] is None:raise DatabaseFixtureError('Disposable database cleanup requires attention')
        return False
