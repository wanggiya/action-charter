"""Trusted fixed inspection reader, not a generated-code execution surface."""
from __future__ import annotations


def main():
    import resource
    import time
    worker_started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (90, 91))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 8 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    import hashlib
    import json
    import sys
    from pathlib import Path
    from geoagent_harness.discovery.source import relative_path
    request = json.loads(sys.stdin.buffer.read(4097))
    path = relative_path(request['path'], 'input')
    if request['action'] not in {'csv_discover','spatial_discover'}:
        resource.setrlimit(resource.RLIMIT_CPU,(10,11))
    if request['action'] in {'csv_probe','csv_discover','spatial_probe','spatial_discover'}:
        spatial=request['action'].startswith('spatial_')
        if spatial:
            from geoagent_harness.discovery.spatial import probe, inspect
        else:
            from geoagent_harness.discovery.csv import probe, inspect
        arguments={} if spatial else {'delimiter':request['delimiter'],'preview_rows':request['preview_rows']}
        if request['action'].endswith('_probe'):
            result=probe(Path(request['root']),path,**arguments)
        else:
            resource.setrlimit(resource.RLIMIT_CPU,(90,91))
            def emit(value):
                fd=request.get('progress_fd')
                if fd is None:return
                import os
                encoded=(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n').encode()
                if len(encoded)>16000:raise ValueError('Metadata exceeds progress budget')
                while encoded:
                    encoded=encoded[os.write(fd,encoded):]
            result=inspect(Path(request['root']),path,**arguments,
                           expected_identity=request.get('source_identity'),on_metadata=emit)
        usage=resource.getrusage(resource.RUSAGE_SELF)
        result['resource_usage']={'worker_seconds':round(time.monotonic()-worker_started,4),'peak_rss_kib':usage.ru_maxrss}
        encoded=json.dumps(result,separators=(',',':'),allow_nan=False)
        if len(encoded.encode())>16000:raise ValueError('Discovery exceeds output budget')
        print(encoded)
        return

    from geoagent_harness.tabular.service import read_bytes, read_frame, _preview
    from .inspection_policy import source_skill
    skill = source_skill(path)
    if skill not in ('inspect_csv', 'inspect_vector', 'inspect_raster'):
        raise ValueError('Unsupported inspection')
    if skill == 'inspect_csv':
        data = read_bytes(Path(request['root']), path)
        digest = hashlib.sha256(data).hexdigest()
        files = {path: data}
    else:
        from .spatial_inspection_snapshot import snapshot
        files, digest = snapshot(Path(request['root']), path)

    if request['action'] == 'snapshot':
        result = {'path': path, 'source_sha256': digest, 'bytes': sum(map(len, files.values()))}
    else:
        if digest != request['source_sha256'] and request['action'] == 'spatial_view':
            print(json.dumps({'error':'The recorded spatial input changed. Its saved evidence remains; run a new inspection before loading a fresh view.'}))
            return
        if digest != request['source_sha256']:
            raise ValueError('The input changed after submission; send a fresh request')
        if request['action'] == 'spatial_view':
            resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
            from .spatial_views import SpatialViewOptions, SpatialDisplayError, render_snapshot
            try:
                result = render_snapshot(path, files, SpatialViewOptions.model_validate(request['view_options']))
            except SpatialDisplayError as error:
                print(json.dumps({'error':str(error)}))
                return
            usage = resource.getrusage(resource.RUSAGE_SELF)
            result['resource_usage'] = {'worker_seconds': round(time.monotonic() - worker_started, 4),
                                        'peak_rss_kib': usage.ru_maxrss}
            encoded = json.dumps(result, separators=(',', ':'), allow_nan=False)
            if len(encoded.encode()) > 500000:
                raise ValueError('Spatial display exceeds its response budget')
            print(encoded)
            return
        if skill != 'inspect_csv':
            resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
            from .spatial_inspection_snapshot import inspect_snapshot
            result = inspect_snapshot(Path(request['root']), path, files)
            result.update(source_sha256=digest, effects='read_only', execution_performed=True,
                          validation_performed=False)
            encoded = json.dumps(result, separators=(',', ':'), allow_nan=False)
            if len(encoded.encode()) > 16000:
                raise ValueError('Spatial inspection response exceeds its budget')
            print(encoded)
            return
        frame = read_frame(data, request['delimiter'])
        preview = _preview(frame, min(20, request['preview_rows']))
        # Full column metadata is separately bounded by the ordinary reader.
        preview['preview'] = [{key: row[key] for key in list(row)[:20]} for row in preview['preview']]
        result = {'operation': 'inspect_csv', 'data_contract': 'table/csv-v1',
                  'source': path, 'source_sha256': digest, **preview,
                  'effects': 'read_only', 'execution_performed': True,
                  'validation_performed': False,
                  'warnings': ['Values are strings; empty fields are missing. Preview is bounded to 20 columns.']}
    encoded = json.dumps(result, separators=(',', ':'))
    if len(encoded.encode()) > 16000:
        raise ValueError('Inspection response exceeds its budget')
    print(encoded)
