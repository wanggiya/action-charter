"""Shared comprehensive profile contract with explicit execution environment."""
import os
from pathlib import Path
from geoagent_harness.contracts.paths import relative_path
from geoagent_harness.workspaces.sandbox.contracts import DatasetOptions
from geoagent_harness.workspaces.sandbox.manager import run_profile, record_artifact

def profile_dataset(root,path,options=None,*,delimiter=',',owner=None,checkpoint=None,max_seconds=120,expected_sha256=None,retain_artifact=True):
    root=Path(root).resolve(strict=True);path=relative_path(path,'input')
    options=DatasetOptions.model_validate(options or {}).model_dump(mode='json')
    if delimiter not in {',','\t'}:raise ValueError('Unsupported delimiter')
    if any(len(tokens)>20 or any(len(v)>200 for v in tokens) for tokens in options['missing_values'].values()):raise ValueError('Missing-token policy exceeds limits')
    if options['codebook_path']:options['codebook_path']=relative_path(options['codebook_path'],'input')
    mode=os.environ.get('ACTIONCHARTER_ANALYTICAL_RUNTIME','docker')
    if mode=='docker':result=run_profile(root,path,options,delimiter=delimiter,checkpoint=checkpoint,max_seconds=max_seconds)
    elif mode=='local':
        from geoagent_harness.workspaces.sandbox.inspection import bounded_read
        result=bounded_read(root,action='dataset_profile',path=path,delimiter=delimiter,analysis=options,max_seconds=max_seconds,checkpoint=checkpoint)
        result['runtime']={'mode':'local_bounded_process','container_isolation':False,'reason':'Explicit trusted compatibility setting'}
    else:raise ValueError('Analytical runtime must be docker or explicit local compatibility mode')
    if expected_sha256 and result['source_sha256']!=expected_sha256:raise ValueError('Source changed since the recorded analytical read')
    # Also supports an existing fixed worker image: guidance uses its recorded
    # complete profiles, without a second scan or weakening the worker boundary.
    from geoagent_harness.data.tabular.field_guidance import guidance_from_profiles
    result['field_guidance']=guidance_from_profiles(result['profiles'],path=result['source'],sha256=result['source_sha256'],source_rows=result['source_rows'],matching_rows=result['matching_rows'])
    from geoagent_harness.data.tabular.readiness import attach_assessment
    attach_assessment(result,result_budget=1024**2)
    if retain_artifact:result['artifact']=record_artifact(root,result,owner)
    return result
