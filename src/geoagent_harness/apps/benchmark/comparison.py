"""Compare validated local observations without inferring a performance winner."""
from geoagent_harness.apps.benchmark.reporting import build_report, STATUSES


def compare_runs(project_root, left_id, right_id):
    if left_id==right_id:raise ValueError('Choose two different benchmark runs')
    left=build_report(project_root,left_id);right=build_report(project_root,right_id)
    reasons=[];a=left['context'];b=right['context']
    if left['evidence_kind']!=right['evidence_kind']:reasons.append('different_evidence_kinds')
    if not left['complete'] or not right['complete']:reasons.append('incomplete_run')
    if a is None or b is None:reasons.append('unrecorded_run_context')
    else:
        for key in ('source_sha256','task_ids','python_version','package_versions','model_configuration',
                    'allow_fixture_writes','disposable_database','include_local_data','review_timeout_seconds'):
            if a[key]!=b[key]:reasons.append('different_'+key)
        if a['review_timeout_seconds'] is None or b['review_timeout_seconds'] is None:
            reasons.append('unrecorded_review_timeout')
        if not a['provider_binding'] or not b['provider_binding']:
            reasons.append('unrecorded_provider_binding')
        elif a['provider_binding']['effective_data_allowed']!=b['provider_binding']['effective_data_allowed']:
            reasons.append('different_effective_data_allowance')
    if left['source_unchanged'] is not True or right['source_unchanged'] is not True:
        reasons.append('unverified_stable_source')
    entries=[]
    l={r['task_id']:r for r in left['results']};r={v['task_id']:v for v in right['results']}
    if l.keys()!=r.keys():reasons.append('different_recorded_task_scope')
    for task in sorted(l.keys()|r.keys()):
        first=l.get(task);second=r.get(task);findings=[]
        if first is None or second is None:findings.append('missing_task_observation')
        else:
            if first['task_sha256']!=second['task_sha256']:findings.append('different_task_definition')
            if first['input_manifest_sha256'] is None or second['input_manifest_sha256'] is None:
                findings.append('unrecorded_input_identity')
            elif first['input_manifest_sha256']!=second['input_manifest_sha256']:
                findings.append('different_input_identity')
            if first['expected_kind']!=second['expected_kind']:findings.append('different_expectation_kind')
            if first['egress_class']!=second['egress_class']:findings.append('different_declared_data_class')
        matched=not findings and not reasons
        both_passed=bool(first and second and first['status']==second['status']=='passed')
        def observation(value):
            if value is None:return None
            return {key:value[key] for key in ('status','reason_code','advisory_status','executed_operations','metrics','failure_details')}
        delta=None
        if matched and both_passed:
            delta={key:(second['metrics'][key]-first['metrics'][key]
                        if first['metrics'][key] is not None and second['metrics'][key] is not None else None)
                   for key in ('model_calls','wall_seconds','prompt_tokens','completion_tokens','process_cpu_seconds')}
        entries.append({'task_id':task,'matched_recorded_conditions':matched,'findings':findings,
                        'both_passed':both_passed,'left':observation(first),'right':observation(second),
                        'right_minus_left_on_matched_passes':delta})
    return {'schema_version':'benchmark-comparison-v1','left':left,'right':right,
            'matched_recorded_conditions':not reasons and all(v['matched_recorded_conditions'] for v in entries),
            'findings':reasons,'tasks':entries,'performance_winner':None,
            'limitations':[
                'Recorded settings, task definitions and staged input identities are compared; no model or workflow is called.',
                'Hardware identity, background load, cache warmth and repeated-run uncertainty are not controlled or inferred.',
                'One observation does not establish model superiority. Deltas are descriptive and only shown for matching successful cases.',
                'Fixture calls are logical test observations, not real model usage. Unknown token/resource measurements stay unknown.',
                'Skipped and unsupported cases are not passes. Critic assessment remains separate from deterministic correctness.',
            ],'model_called':False,'execution_performed':False,'authority_granted':False}


def markdown_comparison(value):
    def label(v):return str(v).replace('|','\\|').replace('`','').replace('\n',' ').replace('\r',' ')
    def number(v):return 'unknown' if v is None else str(round(v,3) if isinstance(v,float) else v)
    lines=['# ActionCharter benchmark comparison','',
           f"Matching recorded conditions: **{str(value['matched_recorded_conditions']).lower()}**.",
           'Performance winner: **not established**.','']
    for side in ('left','right'):
        report=value[side];context=report['context'] or {};binding=context.get('provider_binding')
        identity='unrecorded' if not binding else f"{label(binding['profile_id'])} · revision {binding['provider_revision']} · {label(binding['model'])}"
        lines+=[f"{side.capitalize()}: `{report['run_id']}` · {report['evidence_kind']} · {identity}.",
                'Counts: '+', '.join(f'{k}={report["counts"][k]}' for k in STATUSES)+'.',
                '']
    lines+=['| Run | Reported input/context | Generated output | Reporting tasks (input / output) | Model-call attempts | Task wall seconds |',
            '|---|---:|---:|---|---:|---:|']
    for side in ('left','right'):
        report=value[side];input_usage=report['usage_coverage']['prompt_tokens'];output_usage=report['usage_coverage']['completion_tokens']
        cells=[side,number(input_usage['reported_sum']),number(output_usage['reported_sum']),
               f"{input_usage['tasks_reported']}/{input_usage['tasks_with_calls']} · {output_usage['tasks_reported']}/{output_usage['tasks_with_calls']}",
               number(report['totals']['model_calls']),number(report['totals']['wall_seconds'])]
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['','Token figures sum reported sides only; missing measurements are excluded, not zero.','']
    if value['findings']:lines+=['Unmatched conditions: '+', '.join(value['findings'])+'.','']
    lines+=['| Task | Left status | Right status | Left seconds | Right seconds | Matched conditions |',
            '|---|---|---|---:|---:|---|']
    for row in value['tasks']:
        a=row['left'];b=row['right']
        cells=[row['task_id'],a['status'] if a else 'missing',b['status'] if b else 'missing',
               number(a['metrics']['wall_seconds']) if a else 'unknown',number(b['metrics']['wall_seconds']) if b else 'unknown',
               'yes' if row['matched_recorded_conditions'] else ', '.join(row['findings']) or 'run conditions differ']
        lines.append('| '+' | '.join(label(v) for v in cells)+' |')
    for row in value['tasks']:
        for side in ('left','right'):
            details=(row[side] or {}).get('failure_details')
            if details:
                lines+=['',f"{label(row['task_id'])} · {side} failure: {label(details['stage'])} / {label(details['category'])}.",
                        *['- '+label(text) for text in details['schema_findings']]]
                if details['policy_rule']:lines.append('Policy rule: '+details['policy_rule']+'.')
    lines+=['',*['- '+text for text in value['limitations']],'']
    return '\n'.join(lines)
