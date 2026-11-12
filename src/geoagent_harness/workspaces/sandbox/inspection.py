"""Fixed resource-bounded data access; no workflow eligibility or authority."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from geoagent_harness.contracts.inspection_formats import INSPECTOR_SUFFIXES, source_inspector

# Closed execution adapters: registry read-only status alone is insufficient.
INSPECTION_CONTRACTS = {
    'inspect_csv': {'suffixes': INSPECTOR_SUFFIXES['inspect_csv'], 'version': 'csv-stream-v2', 'max_file_bytes': 1024**3, 'seconds': 120},
    'inspect_vector': {'suffixes': INSPECTOR_SUFFIXES['inspect_vector'], 'version': 'vector-discovery-v2', 'metadata_package_bytes': 1024**3, 'metadata_suffixes': ('.gpkg','.shp'),
                       'max_file_bytes': 8 * 1024**2, 'max_package_bytes': 32 * 1024**2,
                       'max_features': 10000, 'max_layers': 8, 'max_fields': 100},
    'inspect_raster': {'suffixes': INSPECTOR_SUFFIXES['inspect_raster'], 'version': 'raster-discovery-v2', 'metadata_package_bytes': 1024**3, 'metadata_bands': 128,
                       'max_file_bytes': 8 * 1024**2, 'max_bands': 16, 'max_cells': 100_000_000},
}


def source_skill(path):
    return source_inspector(path)


def bounded_read(root, *, action, path, source_sha256=None, delimiter=',', preview_rows=5, checkpoint=None, timeout=30, view_options=None, source_identity=None, on_metadata=None, analysis=None, max_seconds=None):
    from geoagent_harness.contracts.errors import InterfaceApiError
    if sys.platform != 'linux':
        raise InterfaceApiError('Inspection on send currently requires the Linux bounded reader; use reviewed Execute')
    source = str(Path(__import__('geoagent_harness').__file__).resolve().parent.parent)
    command = [sys.executable, '-I', '-B', '-c',
               'import sys;sys.path.insert(0,sys.argv[1]);from geoagent_harness.workspaces.sandbox.inspection_worker import main;main()', source]
    env = {'PATH': str(Path(sys.executable).parent), 'LANG': 'C.UTF-8',
           'PROJ_NETWORK': 'OFF', 'GDAL_PAM_ENABLED': 'NO', 'OGR_SQLITE_VIRTUAL_OGR': 'NO',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    import time
    import os
    if action in {'csv_discover','spatial_discover','dataset_profile'}:
        timeout = 120
    if max_seconds is not None:
        timeout = min(timeout, max_seconds)
    progress_read = progress_write = None
    if on_metadata is not None:
        progress_read, progress_write = os.pipe()
        os.set_blocking(progress_read, False)
    progress_buffer = bytearray()
    def drain():
        if progress_read is None:
            return
        while True:
            try: chunk = os.read(progress_read, 16385)
            except BlockingIOError: break
            if not chunk: break
            progress_buffer.extend(chunk)
            if len(progress_buffer)>16000:
                raise InterfaceApiError('Discovery metadata exceeds its progress budget')
            if b'\n' in progress_buffer:
                line, _, rest = progress_buffer.partition(b'\n')
                progress_buffer[:] = rest
                on_metadata(json.loads(line))
    payload=json.dumps(dict(root=str(root), action=action, path=path, source_sha256=source_sha256,
        source_identity=source_identity, delimiter=delimiter, preview_rows=preview_rows,
        view_options=view_options, progress_fd=progress_write, analysis=analysis)).encode()
    if len(payload) > (16000 if analysis is not None else 4096):
        if progress_read is not None:
            os.close(progress_read);os.close(progress_write)
        raise InterfaceApiError('Inspection request exceeds its worker budget')
    deadline = time.monotonic() + timeout
    from contextlib import ExitStack
    with ExitStack() as resources:
        if progress_read is not None:
            resources.callback(os.close, progress_read)
            resources.callback(os.close, progress_write)
        process=resources.enter_context(subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, cwd='/tmp', close_fds=True, pass_fds=(() if progress_write is None else (progress_write,))))
        try:
            first = True
            while True:
                drain()
                if checkpoint:
                    checkpoint()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise InterfaceApiError(f'Inspection exceeded its {timeout}-second deadline; nothing was retried')
                try:
                    output, _ = process.communicate(payload if first else None, timeout=min(.2, remaining))
                    drain()
                    break
                except subprocess.TimeoutExpired:
                    first = False
            if process.returncode or len(output) > (1024**2 if action=='dataset_profile' else 500000 if action == 'spatial_view' else 128000 if analysis is not None else 16000):
                raise InterfaceApiError('Dataset discovery failed: source changed, unsupported/invalid input or a discovery budget was exceeded. No data was changed.' if action in {'csv_probe','csv_discover','spatial_probe','spatial_discover'} else 'Bounded inspection failed. Check source changes, validity and the 8 MiB per-file and documented feature/layer/band limits. No dataset was changed.')
            result = json.loads(output)
            if result.get('error_code') == 'table_analysis_rejected':
                raise InterfaceApiError(result['error'])
            if action == 'spatial_view' and result.get('error'):
                raise InterfaceApiError(result['error'])
            return result
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


def probe_action(path):
    suffix=Path(path).suffix.lower()
    return 'csv_probe' if suffix in {'.csv','.tsv'} else 'spatial_probe' if suffix in {'.tif','.tiff','.gpkg','.shp'} else 'snapshot'

