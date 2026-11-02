"""Pure analytical and technical documents from recorded workflow evidence."""
import hashlib
import json
from geoagent_harness.tabular.readiness import _cell,_table


def handoff(record):
    from geoagent_harness.redaction import redact_value
    record=redact_value(record)
    technical=['# Workflow technical handoff',_table(['Run','Plan SHA-256','Recorded status'],[[record.get('run_id','not recorded'),record.get('plan_sha256','not recorded'),record.get('status','unknown')]]),
        'Historical evidence, not a current target check or execution authority. A completed operation is not proof of analytical validity.']
    analytical=['# Analytical findings',
        'Each section preserves its own source, filters and denominator. Counts from repeated inspections are not added together. Interpretations and Critic assessments remain separate advisory records.']
    sources={};artifacts=[];omissions=[]
    steps=record.get('steps',[])
    for step in steps:
        outcome=step.get('outcome') or {};identity=step['step_id'];skill=step.get('skill_id',step.get('skill','unknown'))
        technical += ['## '+_cell(identity+' · '+skill), 'Status: '+_cell(step.get('status','unknown'))]
        if outcome.get('preview_omitted'):
            technical += ['Recorded step detail was omitted by its display budget; consult original durable evidence. Missing detail is not a passing check.']
        for source in outcome.get('sources',[]):
            sources[source['path'],source['sha256']]=source
        if outcome.get('source_sha256') and outcome.get('source'):
            sources[outcome['source'],outcome['source_sha256']]={'path':outcome['source'],'sha256':outcome['source_sha256']}
        if outcome.get('output'):
            artifacts.append({'step_id':identity,**outcome['output']})
        if outcome.get('streaming_preparation'):
            technical += ['Preparation: '+_cell(json.dumps(outcome['streaming_preparation'],sort_keys=True))]
        if outcome.get('codebook_coverage'):
            technical += ['Codebook coverage: '+_cell(json.dumps(outcome['codebook_coverage'],sort_keys=True))]
        validation=step.get('validation_outcome') or {}
        technical += ['Validation: '+_cell(json.dumps(validation,sort_keys=True))]
        if outcome.get('proposed_ddl'):
            technical += ['Proposed table definition (preflight only):',_cell(outcome['proposed_ddl'])]
        if outcome.get('column_metadata'):
            if outcome.get('executed_ddl'):
                technical += ['Executed CREATE statement (generated from the reviewed typed mapping):',_cell(outcome['executed_ddl'])]
            technical += ['Recorded database table: '+_cell(str(outcome.get('target_schema'))+'.'+str(outcome.get('target_table'))),
                _table(['Column','Observed PostgreSQL type','Nullable'],[[c['name'],c['type'],c['nullable']] for c in outcome['column_metadata']]),
                'Recorded keys: '+_cell(json.dumps(outcome.get('key_constraints',[]),sort_keys=True)),
                _table(['Rows','Table SHA-256','Semantic SHA-256','Committed'],[[outcome.get(k) for k in ('row_count','table_sha256','semantic_sha256','committed')]]),
                'Column defaults, foreign keys, non-key indexes and grants are not fully captured by this adapter; this is a recorded schema description, not a complete database backup.']
        if outcome.get('arguments'):
            technical += ['Executed mapping/parameters: '+_cell(json.dumps(outcome['arguments'],sort_keys=True))]
        ready=outcome.get('readiness_assessment') or {}
        stats=((outcome.get('table_analysis') or {}).get('statistics') or {})
        if ready.get('report_markdown'):
            analytical += ['## '+_cell(identity),ready['report_markdown']]
        if stats.get('report_markdown') and (not ready or ready.get('omissions',{}).get('statistical_report')):
            analytical += ['## '+_cell(identity+' · statistical method details'),stats['report_markdown']]
    technical += ['## Source identities',_table(['Source','SHA-256'],[[p,h] for p,h in sources]),
        '## Produced files',_table(['Step','Path','SHA-256'],[[a['step_id'],a['path'],a['sha256']] for a in artifacts]),
        '## Reproduction and recovery',
        'Use the saved exact workflow and declared source/codebook identities. Review actual operation arguments, types, null policy and source scope before a new run. Fresh targets and fresh write authorization are required; this document never replays a workflow.',
        'If a write committed before a later failure, preserve its receipt and inspect the actual target. An uncertain commit is not proof of rollback. Never automatically retry writes or reuse expired/mismatched authority. No passwords, connection strings or secret file contents are embedded here.']
    if not any((s.get('outcome') or {}).get('readiness_assessment') or ((s.get('outcome') or {}).get('table_analysis') or {}).get('statistics') for s in steps):
        analytical += ['No source-bound statistical/readiness report was recorded in these steps. No findings were invented or recomputed.']
    documents={}
    for name,parts in [('technical_markdown',technical),('analytical_markdown',analytical)]:
        retained=[];used=0
        for part in parts:
            size=len(part.encode())+2
            if used+size>256000:
                omissions.append(name);break
            retained.append(part);used+=size
        if len(retained)<len(parts):retained.append('Document display budget reached. Consult original saved step evidence; omitted material is not a passing check.')
        documents[name]='\n\n'.join(retained)+'\n'
    return {'schema_version':'workflow-handoff-v1','run_id':record.get('run_id','not recorded'),'plan_sha256':record.get('plan_sha256'),
        'status':record.get('status','unknown'),**documents,'omitted_documents':omissions,'execution_performed':False,'authority_granted':False,
        'report_sha256':hashlib.sha256(json.dumps(documents,sort_keys=True).encode()).hexdigest()}
