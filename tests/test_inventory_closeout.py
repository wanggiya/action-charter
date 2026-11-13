"""Partial display inventories preserve evidence and never authorize invalid files."""
import hashlib
import json
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest

from tests.test_task_agents import project
from tests.test_recipe_storage import make_recipe
from tests.test_interface_api import reviewed_plan_request
from geoagent_harness.core.ledger.recipe_storage import save_recipe, load_recipe, MAX_RECIPE_BYTES
from geoagent_harness.core.policy.recipe import validate_recipe_policy, RecipePolicyError
from geoagent_harness.platform.skill_registry import load_skill_registry
from geoagent_harness.task_actions.legacy_planning import interface_saved_recipe_inventory, interface_saved_plan_inventory
from geoagent_harness.task_actions.artifacts import prepare_interface_recipe_approval, save_interface_reviewed_plan
from geoagent_harness.contracts.errors import InterfaceApiError


def seed(root):
    valid = make_recipe()
    _, good = save_recipe(valid, recipe_root=root/'workflow-recipes')
    bad = valid.model_copy(deep=True)
    bad.recipe_id = 'legacy-csv-inspection'
    bad.steps[0].arguments['path'] = 'data/input/sample_orders.csv'
    _, invalid = save_recipe(bad, recipe_root=root/'workflow-recipes')
    return good, invalid


def hashes(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file() and not p.is_symlink()}


def test_mixed_policy_records_preserve_bytes_and_approval_boundary(project):
    good, bad = seed(project)
    before = hashes(good.parent)
    result = interface_saved_recipe_inventory(project_root=project)
    assert result['recipe_count'] == 1 and result['recipes'][0]['recipe_filename'] == good.name
    assert result['invalid_record_count'] == 1
    finding = result['invalid_records'][0]
    assert finding['filename'] == bad.name and finding['code'] == 'policy_rejected'
    assert 'inspect_csv' in finding['reason'] and not finding['execution_allowed'] and not finding['approval_allowed']
    with pytest.raises(RecipePolicyError):
        validate_recipe_policy(load_recipe(bad, recipe_root=bad.parent), registry=load_skill_registry(project))
    with pytest.raises((RecipePolicyError, ValueError, RuntimeError)):
        prepare_interface_recipe_approval(recipe_filename=bad.name,
            confirmed_recipe_sha256=bad.name.split('.')[-2], project_root=project)
    assert hashes(good.parent) == before
    assert not (project/'approvals').exists()
    assert not result['recipe_modified'] and not result['approval_performed'] and not result['execution_performed']


def test_malformed_symlink_oversize_and_approval_records_do_not_break_list(project):
    good, bad = seed(project)
    (good.parent/'broken.json').write_text('{"password":"never-display-this-secret",')
    outside = project/'private.json';outside.write_text('never-display-this-secret')
    (good.parent/'linked.json').symlink_to(outside)
    huge = good.parent/'huge.json'
    with huge.open('wb') as f:f.truncate(MAX_RECIPE_BYTES+1)
    approvals = project/'approvals';approvals.mkdir()
    (approvals/'recipe-approval-broken.json').write_text('{')
    before = hashes(good.parent)
    result = interface_saved_recipe_inventory(project_root=project)
    assert result['recipe_count'] == 1 and result['invalid_record_count'] == 5
    assert len(result['invalid_records']) == 5
    assert 'never-display-this-secret' not in json.dumps(result)
    assert all(not f['execution_allowed'] and len(f['reason']) <= 300 for f in result['invalid_records'])
    assert hashes(good.parent) == before and outside.read_text() == 'never-display-this-secret'


def test_invalid_plan_and_plan_approval_keep_valid_plans_visible(project):
    saved = save_interface_reviewed_plan(reviewed_plan_request(), project_root=project)
    plans = project/'plans';(plans/'planner-plan.broken.json').write_text('{')
    approvals = project/'approvals';approvals.mkdir()
    (approvals/'approval-broken.json').write_text('{')
    result = interface_saved_plan_inventory(project)
    assert result['plan_count'] == 1 and result['plans'][0]['plan_sha256'] == saved['plan_sha256']
    assert {r['kind'] for r in result['invalid_records']} == {'plan', 'plan_approval'}
    assert not result['files_modified'] and not result['execution_performed']
    from geoagent_harness.task_actions.artifacts import _planner_recipe_definition
    recipe = _planner_recipe_definition(reviewed_plan_request().planner_result, saved['plan_sha256'])
    save_recipe(recipe, recipe_root=project/'workflow-recipes')
    matching = plans/('planner-plan.' + saved['plan_sha256'][:16] + 'f' * 48 + '.json')
    matching.write_text('{')
    listing = interface_saved_recipe_inventory(project_root=project)
    assert listing['recipe_count'] == 1
    assert listing['recipes'][0]['plan_definition_link'] == 'blocked'
    assert listing['recipes'][0]['matching_plan_sha256'] is None
    assert any(r['kind'] == 'plan' for r in listing['invalid_records'])


def test_all_invalid_is_visible_and_unsafe_root_still_fails_closed(project):
    directory = project/'workflow-recipes';directory.mkdir();(directory/'broken.json').write_text('{')
    result = interface_saved_recipe_inventory(project_root=project)
    assert result['recipes'] == [] and result['invalid_record_count'] == 1
    linked = project/'linked-root';linked.symlink_to(directory, target_is_directory=True)
    with pytest.raises(InterfaceApiError, match='unsafe'):
        interface_saved_recipe_inventory(project_root=project, recipe_root=linked)


def test_deeply_nested_record_is_unavailable_without_leaking_or_crashing(project):
    good, _ = seed(project)
    import sys
    depth = sys.getrecursionlimit() + 20
    (good.parent/'nested.json').write_text('{"nested":' + '[' * depth + '0' + ']' * depth + '}')
    result = interface_saved_recipe_inventory(project_root=project)
    assert result['recipe_count'] == 1
    finding = next(r for r in result['invalid_records'] if r['filename'] == 'nested.json')
    assert finding['code'] == 'invalid_record' and finding['reason'] and not finding['execution_allowed']


def test_diagnostic_count_is_bounded_without_hiding_omissions(project):
    seed(project)
    approvals = project/'approvals';approvals.mkdir()
    for i in range(205):
        (approvals/f'recipe-approval-broken-{i}.json').write_text('{')
    result = interface_saved_recipe_inventory(project_root=project)
    assert result['recipe_count'] == 1 and result['invalid_record_count'] == 206
    assert len(result['invalid_records']) == 200 and result['invalid_records_truncated']


def test_real_http_endpoint_returns_200_and_does_not_execute(project):
    from geoagent_harness.apps.http.server import _handler
    from http.server import ThreadingHTTPServer
    good, bad = seed(project)
    before = hashes(good.parent)
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(project))
    thread = Thread(target=server.serve_forever, daemon=True);thread.start()
    try:
        with urlopen(f'http://127.0.0.1:{server.server_port}/api/v1/recipes') as response:
            assert response.status == 200
            result = json.load(response)
        assert result['recipe_count'] == result['invalid_record_count'] == 1
        assert hashes(good.parent) == before and not (project/'approvals').exists()
    finally:
        server.shutdown();server.server_close();thread.join()
