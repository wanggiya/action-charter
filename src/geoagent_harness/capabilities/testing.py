"""Resource-bounded tests for data-only text definitions, never model Python."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys


def test_text_package(package, timeout_seconds=20):
    from geoagent_harness.operations.packages import canonical, PackageError, package_sha
    if sys.platform != 'linux':raise PackageError('The bounded acquisition test worker currently requires Linux resource limits')
    source=str(Path(__file__).resolve().parents[2])
    command=[sys.executable,'-I','-B','-c',
        'import sys;sys.path.insert(0,sys.argv[1]);from geoagent_harness.capabilities.worker import main;main()',source]
    env={'PATH':str(Path(sys.executable).parent),'LANG':'C.UTF-8','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
    try:
        result=subprocess.run(command,input=canonical(package),capture_output=True,timeout=min(20,timeout_seconds),env=env,cwd='/tmp')
    except subprocess.TimeoutExpired as error:raise PackageError('Candidate fixture worker exceeded its 20-second deadline') from error
    if result.returncode or len(result.stdout)>32000:raise PackageError('Candidate fixture worker failed its process/resource/output bounds')
    try:report=json.loads(result.stdout)
    except (ValueError,UnicodeError) as error:raise PackageError('Candidate fixture worker returned invalid evidence') from error
    if report.get('package_sha256')!=package_sha(package):
        raise PackageError('Fixture report does not match the candidate')
    return report
