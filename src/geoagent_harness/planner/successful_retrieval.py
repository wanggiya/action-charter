"""Bounded, own-conversation retrieval of recorded methods, never execution."""
import json
import re
from pathlib import Path

from geoagent_harness.context_pack.redaction import redact_value
from geoagent_harness.recipe_catalog.successful import inventory, digest


def retrieve(root, conversation_id, message, available, *, use_history=True, selected_id=None):
    legacy = re.search(r'\bsaved successful method ([a-f0-9]{64})\b', message)
    explicit = selected_id or (legacy[1] if legacy else None)
    receipt = {'status':'none','count':0,'method_ids':[],'bytes':0,'explicit_selection':bool(explicit)}
    if not use_history and not explicit:
        return [], {**receipt,'status':'history_disabled'}
    words=set(re.findall(r'[a-z]{3,}',message.casefold()))
    aliases={'clean':'cleaning','inspect':'inspection','aggregate':'aggregation','sum':'aggregation','group':'aggregation','table':'csv','columns':'csv','missing':'cleaning'}
    words.update(aliases[word] for word in list(words) if word in aliases)
    try:
        candidates=inventory(root,conversation_id=conversation_id)
    except Exception:
        return [], {**receipt,'status':'index_unavailable'}
    matches=[]
    for record in candidates:
        if record['contract_status']!='current' or any(o['skill_id'] not in available for o in record['operations']):continue
        score=len(words & set(record['tags']))
        if explicit:
            if record['method_id']!=explicit:continue
            score=100
        if score:matches.append((score,record))
    if not matches:
        return [], {**receipt,'status':'selection_unavailable' if explicit else 'none'}
    matches.sort(key=lambda item:(-item[0],item[1]['method_id']))
    from geoagent_harness.interface_api.server import InterfaceApiError
    from geoagent_harness.interface_api.workflow_runs import _directory,_read
    from geoagent_harness.operations.registry import argument_models
    models=argument_models(root)
    snippets=[]
    for _,record in matches[:3]:
        # A grouping can have several observations; use the latest verified source.
        source=max(record['sources'],key=lambda s:s['finished_at'])
        if re.fullmatch(r'[a-f0-9]{32}',source['run_id']) is None:continue
        try:
            run=_read(_directory(root),source['run_id'])
            if run.get('conversation_id')!=conversation_id or run['status']!='completed' or run['plan_sha256']!=source['plan_sha256']:continue
            observed={'plan_sha256':run['plan_sha256'],'steps':[{k:s.get(k) for k in ('step_id','skill_id','status','outcome','validation_outcome')} for s in run['steps']]}
            if digest(observed)!=source['evidence_sha256']:continue
            if not run.get('retention_basis') or run['retention_basis']['method_id']!=record['method_id']:continue
            steps=[]
            for step in run['steps']:
                arguments=models[step['skill_id']].model_validate(step['arguments']).model_dump(mode='json',exclude_none=True)
                # Old target bindings are not a proposal for the next attempt.
                suffix=Path(arguments['target_path']).suffix if isinstance(arguments.get('target_path'),str) else None
                arguments={k:v for k,v in arguments.items() if k not in {'target_path','schema_name','table_name','target_schema','target_table'} and not re.search(r'password|secret|token|credential|approval',k,re.I)}
                steps.append({'step_id':step['step_id'],'skill':step['skill_id'],'arguments':redact_value(arguments),'depends_on':step.get('depends_on') or [],'previous_output_suffix':suffix})
            snippet={'method_id':record['method_id'],'name':record['name'],'tags':record['tags'],'source_run_id':source['run_id'],
                     'source_plan_sha256':source['plan_sha256'],'evidence_sha256':source['evidence_sha256'],'historical_operations':steps,
                     'limitations':'Own-chat recorded success only. Recheck inputs/columns/contracts. Supply fresh output bindings. No authority or general applicability.'}
            annotation=record.get('critic_annotation')
            if annotation and annotation.get('run_id')==source['run_id'] and annotation.get('evidence_sha256')==source['evidence_sha256']:
                snippet['advisory_method_note']=redact_value({key:annotation[key] for key in ('title','purpose','limitations','model','evidence_kind','execution_authority_granted')})
            if len(json.dumps(snippets+[snippet]).encode())>8000:continue
            snippets.append(snippet)
        except (ValueError,OSError,KeyError,TypeError,InterfaceApiError):
            continue
    receipt.update(status='included' if snippets else ('selection_unavailable' if explicit else 'none'),count=len(snippets),
                   method_ids=[s['method_id'] for s in snippets],bytes=len(json.dumps(snippets).encode()))
    return snippets,receipt
