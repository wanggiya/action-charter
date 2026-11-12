"""Complete recorded basic quality; fixtures only, no model, DB or owner data."""
import copy
import hashlib
import json
import math

import pytest

from geoagent_harness.capabilities.recipes.execution.handoff import handoff
from geoagent_harness.data.discovery.csv import inspect
from geoagent_harness.data.tabular.basic_profile import BasicProfile, recorded_report


@pytest.fixture
def source(tmp_path):
    folder = tmp_path / 'data/input'
    folder.mkdir(parents=True)
    (folder / 'facts.csv').write_text('encounter_id,patient_nbr,age,ward_id,value,label\n'
        '001,A,[40-50),1,2,x\n001,A,[40-50),1,2,x\n'
        '002,A,[50-60),2,4,\n003,B,[50-60),2,?,NA\n004,B,[50-60),2,6,x\n')
    return tmp_path


def record(result):
    return {'run_id': 'fixture', 'plan_sha256': 'a' * 64, 'status': 'completed',
        'steps': [{'step_id': 'step_1', 'skill_id': 'inspect_csv', 'status': 'completed', 'outcome': result}]}


def test_plain_inspection_collects_complete_quality_and_mean_without_semantic_coercion(source):
    result = inspect(source, 'facts.csv', preview_rows=1)
    profile = result['basic_profile']
    fields = {f[0]: f for f in profile['fields']}
    assert result['row_count'] == profile['rows'] == 5 and len(result['preview']) == 1
    assert profile['source_sha256'] == hashlib.sha256((source/'data/input/facts.csv').read_bytes()).hexdigest()
    assert fields['encounter_id'][2:] == [4, 3, 1, 1]
    assert fields['patient_nbr'][2:] == [2, 0, 2, 3]
    assert fields['label'][2:] == [2, 1, 1, 2]  # NA remains a real distinct value
    assert fields['value'][2:] == [4, 3, 1, 1]  # ? remains a distinct value
    assert profile['duplicate_rows'] == [4, 3, 1, 1]
    assert fields['age'][1] == 'ordered_category' and fields['ward_id'][1] == 'categorical'
    assert fields['patient_nbr'][1] == 'identifier'
    assert set(profile['numeric']) == {'value'}
    count, mean, minimum, maximum, sd, invalid = profile['numeric']['value']
    assert [count, mean, minimum, maximum, invalid] == [4, 3.5, 2., 6., 1]
    assert sd == pytest.approx(math.sqrt(11/3))
    assert result['missing_counts']['value'] == 0 and result['missing_counts']['label'] == 1
    assert len(json.dumps(result, separators=(',', ':')).encode()) < 16000
    report = recorded_report(result)
    assert '| label |' in report and '| 1 | 20.0 |' in report
    assert 'Sample standard deviation' in report and 'Not calculated' not in report.split('## Whole-row duplicates')[1].split('## Numerical summaries')[0]
    assert 'P-values' in report and 'patient/entity key' in report
    assert not (source/'data/output').exists()


def test_declared_policy_and_filtered_analysis_keep_separate_denominators(source):
    result = inspect(source, 'facts.csv', analysis={'missing_values': {'value': ['?']},
        'filters': [{'column': 'label', 'value': 'x'}]})
    basic = result['basic_profile']
    assert basic['rows'] == 5 and result['table_analysis']['matched_row_count'] == 3
    assert next(f for f in basic['fields'] if f[0] == 'value')[2] == 3
    assert basic['missing_values'] == {'value': ['?']}
    assert basic['numeric']['value'][-1] == 0
    assert 'Complete source basic quality' in result['readiness_assessment']['report_markdown']
    assert 'recorded complete table' in result['readiness_assessment']['report_markdown']


def test_legacy_report_is_pure_and_explicit_about_absent_checks(source, monkeypatch):
    result = inspect(source, 'facts.csv')
    result.pop('basic_profile')
    original = copy.deepcopy(result)
    (source/'data/input/facts.csv').unlink()
    from geoagent_harness.data.tabular import inspection
    monkeypatch.setattr(inspection, 'inspect_table', lambda *a, **k: pytest.fail('report must not read'))
    report = handoff(record(result))
    text = report['analytical_markdown']
    assert 'Recorded inspection quality' in text and 'Missing %' in text
    assert 'Once-only values' in text and 'Not calculated' in text
    assert 'No basic numerical summaries recorded' in text
    assert 'zero-duplicate result' in text and 'No source was reread' in text
    assert report == handoff(record(result)) and result == original
    assert not report['execution_performed'] and not report['authority_granted']


def test_mismatched_profile_is_not_used_and_untrusted_labels_are_escaped(source):
    result = inspect(source, 'facts.csv')
    result['basic_profile']['source_sha256'] = 'b' * 64
    result['field_guidance']['source_sha256'] = 'b' * 64
    result['columns'][0] = '<script>|field\n'
    report = recorded_report(result)
    assert 'No basic numerical summaries recorded' in report
    assert '<script>' not in report and '&lt;script&gt;&#124;field' in report


def test_counter_budget_exhaustion_keeps_full_missing_and_numeric_results(source, monkeypatch):
    from geoagent_harness.data.tabular import inspection
    monkeypatch.setattr(inspection, 'BasicProfile', lambda names, missing: BasicProfile(names, missing, max_entries=0))
    result = inspect(source, 'facts.csv')
    assert result['row_count'] == 5 and result['missing_counts']['label'] == 1
    assert result['basic_profile']['duplicate_rows'] == [None] * 4
    assert all(f[2:] == [None] * 4 for f in result['basic_profile']['fields'])
    assert result['basic_profile']['numeric']['value'][1] == 3.5
    report = recorded_report(result)
    assert 'counter budget exceeded' in report and 'Not calculated / budget limited' in report


def test_fifty_column_profile_fits_worker_budget_and_does_not_drop_end_fields(source):
    names = [f'column_{i}' for i in range(50)]
    path = source/'data/input/wide.csv'
    path.write_text(','.join(names)+'\n'+('\n'.join(','.join(str(i+j) for j in range(50)) for i in range(100)))+'\n')
    result = inspect(source, 'wide.csv')
    assert result['basic_profile']['omitted_fields'] == 0
    assert len(result['basic_profile']['fields']) == 50
    assert len(json.dumps(result, separators=(',', ':')).encode()) < 16000
    assert 'column_49' in recorded_report(result)


def test_native_null_and_empty_string_remain_distinct_in_duplicates(source):
    from geoagent_harness.data.tabular.inspection import inspect_table
    (source/'data/input/native.json').write_text('[{"value":null},{"value":""},{"value":2},{"value":2}]')
    result = inspect_table(source, 'native.json')
    assert result['basic_profile']['duplicate_rows'] == [3, 2, 1, 1]
    assert result['missing_counts'] == {'value': 1}
    assert result['empty_string_counts'] == {'value': 1}
    report = recorded_report(result)
    assert 'native nulls' in report and 'Empty text' in report


def test_empty_and_single_numeric_observation_do_not_invent_spread(source):
    path = source/'data/input/tiny.csv'
    path.write_text('value\n2\n')
    result = inspect(source, 'tiny.csv')
    assert result['basic_profile']['numeric']['value'][4] is None
    path.write_text('value\n')
    result = inspect(source, 'tiny.csv')
    assert result['basic_profile']['duplicate_rows'] == [0, 0, 0, 0]
    assert not result['basic_profile']['numeric']
    assert 'Unavailable' in recorded_report(result)  # undefined percentages, not zero


def test_redaction_and_durable_preview_budget_keep_reports_usable(source):
    from geoagent_harness.task_actions.workflow_runs import fit_table_preview
    from geoagent_harness.platform.outcomes import _bounded_outcome
    path = source/'data/input/redacted.csv'
    path.write_text('token,value\n?,2\n3,4\n3,6\n')
    result = inspect(source, 'redacted.csv')
    text = handoff(record(result))['analytical_markdown']
    assert '[REDACTED]' in text and 'Recorded inspection quality' in text
    assert 'Sample standard deviation' in text
    bounded = _bounded_outcome(fit_table_preview(result))
    assert len(json.dumps(bounded).encode()) <= 16000
    assert bounded['basic_profile']['rows'] == 3


def test_registered_mcp_report_reads_the_same_durable_quality_without_source(source):
    from types import SimpleNamespace
    from geoagent_harness.task_actions import data_tools, workflow_runs
    result = inspect(source, 'facts.csv')
    saved = record(result)
    saved['run_id'] = 'a' * 32
    directory = workflow_runs._directory(source)
    workflow_runs._write(directory, saved, project_root=source)
    (source/'data/input/facts.csv').unlink()
    value = data_tools.workflow_report(saved['run_id'], settings=SimpleNamespace(project_root=source))
    assert value['handoff'] == handoff(saved)
    assert 'Whole-row duplicates' in value['handoff']['analytical_markdown']
    assert not value['handoff']['execution_performed']
