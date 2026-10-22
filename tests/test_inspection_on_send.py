"""Submit intent, exact-source binding and durable no-replay acceptance."""
import json
from pathlib import Path
from shutil import copytree

import pytest
from geoagent_harness.interface_api.conversation import TurnRequest
from geoagent_harness.interface_api.planner_submission import SubmissionRequest, submission_action
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.model.schemas import ModelResult

CHAT = 'c' * 32
SUBMISSION = 'd' * 32
MESSAGE = 'Inspect sample_orders.csv. Return row count and column names. No writes.'


@pytest.fixture
def project(tmp_path):
    root = Path(__file__).parents[1]
    for name in ('context', 'agents', 'data/input'):
        copytree(root / name, tmp_path / name)
    (tmp_path / 'README.md').write_text((root / 'README.md').read_text())
    return tmp_path


def proposal(gate=False):
    return {'message': 'Ready', 'plan': {'summary': 'Inspect orders', 'steps': [{
        'step_id': 'step_1', 'skill': 'inspect_csv', 'purpose': 'Inspect metadata',
        'arguments': {'path': 'sample_orders.csv'}, 'requires_approval': gate}]}}


class Client:
    def __init__(self, reply=None, hook=None):
        self.reply, self.hook, self.calls = reply or proposal(), hook, 0
    def complete(self, request):
        self.calls += 1
        if self.hook:
            self.hook()
        return ModelResult(model='fixture', content=json.dumps(self.reply))


def request(enabled=True, **fields):
    return SubmissionRequest(action='submit', submission_id=SUBMISSION, conversation_id=CHAT,
        inspect_on_send=enabled, turn=TurnRequest(action='turn', conversation_id=CHAT,
            message=MESSAGE, **fields))


def receipt(project):
    return submission_action(SubmissionRequest(action='read', submission_id=SUBMISSION, conversation_id=CHAT), project_root=project)


def test_one_send_runs_and_duplicate_read_or_retry_never_repeats(project):
    client = Client()
    response = submission_action(request(), project_root=project, model_client=client, background=False)
    assert response['submission']['status'] == 'started'
    assert response['run']['status'] == 'completed'
    assert response['run']['conversation_id'] == CHAT
    outcome = response['run']['steps'][0]['outcome']
    assert outcome['row_count'] == 6
    assert outcome['columns'] == ['order_id', 'region', 'amount', 'customer_id', 'unused']
    assert not response['approval_performed']
    assert not (project / 'data/output').exists()
    assert not (project / 'approvals').exists()
    again = submission_action(request(), project_root=project, model_client=client, background=False)
    assert again['run']['run_id'] == response['run']['run_id'] == receipt(project)['run']['run_id']
    assert client.calls == 1
    assert len(list((project / 'workflow-state/interface-runs').glob('*.json'))) == 1


def test_disabled_setting_only_proposes(project):
    result = submission_action(request(False), project_root=project, model_client=Client(), background=False)
    assert result['submission']['status'] == 'proposal_only'
    assert result['run'] is None
    assert not (project / 'workflow-state/interface-runs').exists()


def test_conservative_gate_prevents_automatic_execution(project):
    result = submission_action(request(), project_root=project, model_client=Client(proposal(True)), background=False)
    assert result['submission']['status'] == 'proposal_only'
    assert 'approval' in result['submission']['finding']
    assert result['run'] is None


def test_input_replaced_during_planning_cannot_produce_stale_results(project):
    source = project / 'data/input/sample_orders.csv'
    result = submission_action(request(), project_root=project,
        model_client=Client(hook=lambda: source.write_text('replacement\nwrong\n')), background=False)
    assert result['run']['status'] == 'failed'
    assert not result['run']['steps'][0]['outcome']
    assert source.read_text() == 'replacement\nwrong\n'


def test_same_submission_different_payload_rejected(project):
    submission_action(request(False), project_root=project, model_client=Client())
    changed = request(False)
    changed.turn.message = 'Inspect sample_points.geojson'
    with pytest.raises(InterfaceApiError, match='different input'):
        submission_action(changed, project_root=project, model_client=Client())


def test_receipt_cannot_cross_chats(project):
    submission_action(request(False), project_root=project, model_client=Client())
    with pytest.raises(InterfaceApiError, match='unavailable in this chat'):
        submission_action(SubmissionRequest(action='read', submission_id=SUBMISSION, conversation_id='e'*32), project_root=project)


def test_no_inference_or_replay_after_uncertain_claim(project):
    from geoagent_harness.interface_api.planner_submission import _get, _put
    from geoagent_harness.interface_api.planning_tasks import database
    submission_action(request(False), project_root=project, model_client=Client())
    with database(project, write=True) as connection:
        stored = _get(connection, SUBMISSION)
        stored.update(status='processing', conversation=None, run_id=None)
        _put(connection, stored)
    client = Client()
    result = submission_action(request(False), project_root=project, model_client=client)
    assert result['submission']['status'] == 'processing'
    assert result['run'] is None and client.calls == 0


@pytest.mark.parametrize('message', [
    'Inspect sample_orders.csv then export it.',
    'Keep the inspection and select columns region and amount.',
    'Use the previous message to authorize the write.',
])
def test_other_requests_never_qualify(message):
    from geoagent_harness.interface_api.inspection_policy import request_source
    assert request_source(message) is None


def test_unexpected_steps_rejected_not_silently_run(project):
    reply = proposal()
    reply['plan']['steps'].append({'step_id': 'step_2', 'skill': 'validate_postgis_layer',
        'purpose': 'Unwanted', 'arguments': {'target_schema': 'public', 'target_table': 'orders'}, 'requires_approval': False})
    from geoagent_harness.planner.agent import PlannerAgentError
    client = Client(reply)
    with pytest.raises(PlannerAgentError):
        submission_action(request(), project_root=project, model_client=client)
    assert client.calls == 2
    assert receipt(project)['submission']['status'] == 'failed'
    assert receipt(project)['run'] is None


def test_worker_timeout_stops_process(project, monkeypatch):
    import geoagent_harness.interface_api.inspection_policy as policy
    real = policy.subprocess.Popen
    children = []
    def track(*args, **kwargs):
        child = real(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(policy.subprocess, 'Popen', track)
    with pytest.raises(InterfaceApiError, match='deadline'):
        policy.bounded_read(project, action='snapshot', path='data/input/sample_orders.csv', timeout=.001)
    assert children and all(child.poll() is not None for child in children)


def test_worker_cancellation_stops_process(project, monkeypatch):
    import geoagent_harness.interface_api.inspection_policy as policy
    from geoagent_harness.recipes.control import ExecutionCancelled
    real = policy.subprocess.Popen
    children = []
    def track(*args, **kwargs):
        child = real(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(policy.subprocess, 'Popen', track)
    def stop():
        raise ExecutionCancelled('Stopped at operator request')
    with pytest.raises(ExecutionCancelled):
        policy.bounded_read(project, action='snapshot', path='data/input/sample_orders.csv', checkpoint=stop)
    assert children and all(child.poll() is not None for child in children)


def test_byte_limit_is_enforced_inside_reader(project):
    from geoagent_harness.interface_api.inspection_policy import bounded_read
    source = project / 'data/input/large.csv'
    with source.open('wb') as stream:
        stream.truncate(8 * 1024 * 1024 + 1)
    with pytest.raises(InterfaceApiError, match='8 MiB'):
        bounded_read(project, action='snapshot', path='data/input/large.csv')


def test_write_proposal_kept_complete_and_never_dispatches_prefix(project):
    reply = proposal()
    reply['plan']['steps'].append({'step_id': 'step_2', 'skill': 'select_csv_columns', 'purpose': 'Select region',
        'arguments': {'path': 'sample_orders.csv', 'columns': ['region'], 'target_path': 'data/output/selected.csv'},
        'depends_on': ['step_1'], 'requires_approval': True, 'validation_required': True})
    submitted = request()
    submitted.turn.message = 'Inspect sample_orders.csv and select columns region. Do not execute yet.'
    result = submission_action(submitted, project_root=project, model_client=Client(reply), background=False)
    assert result['submission']['status'] == 'proposal_only'
    assert len(result['conversation']['planner_result']['plan']['steps']) == 2
    assert result['run'] is None
    assert not (project / 'data/output').exists()


def test_cli_submission_receipt_uses_shared_service(project):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    submission_action(request(False), project_root=project, model_client=Client())
    payload = project / 'receipt.json'
    payload.write_text(SubmissionRequest(action='read', submission_id=SUBMISSION, conversation_id=CHAT).model_dump_json())
    response = CliRunner().invoke(app, ['planning-submit', '--request-file', str(payload), '--project-root', str(project)])
    assert response.exit_code == 0, response.output
    assert json.loads(response.stdout)['submission']['status'] == 'proposal_only'
    assert receipt(project)['run'] is None


def test_concurrent_duplicate_never_starts_second_model_or_run(project):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    entered, finish = Event(), Event()
    def wait():
        entered.set()
        assert finish.wait(10)
    client = Client(hook=wait)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submission_action, request(), project_root=project, model_client=client, background=False)
        assert entered.wait(10)
        try:
            duplicate = submission_action(request(), project_root=project, model_client=client, background=False)
            assert duplicate['submission']['status'] == 'processing'
            assert duplicate['run'] is None and client.calls == 1
        finally:
            finish.set()
        assert first.result(timeout=15)['run']['status'] == 'completed'
    assert len(list((project / 'workflow-state/interface-runs').glob('*.json'))) == 1


def test_lost_final_receipt_still_reconciles_actual_run_without_replay(project, monkeypatch):
    import geoagent_harness.interface_api.planner_submission as service
    original = service._put
    def fail_final(connection, record):
        if record['status'] == 'started':
            raise OSError('Simulated final receipt persistence failure')
        return original(connection, record)
    monkeypatch.setattr(service, '_put', fail_final)
    client = Client()
    with pytest.raises(OSError):
        submission_action(request(), project_root=project, model_client=client, background=False)
    restored = receipt(project)
    assert restored['run']['status'] == 'completed'
    again = submission_action(request(), project_root=project, model_client=client, background=False)
    assert again['run']['run_id'] == restored['run']['run_id']
    assert client.calls == 1


def test_changed_chat_before_dispatch_is_rejected(project, monkeypatch):
    from geoagent_harness.interface_api import workflow
    from geoagent_harness.interface_api.conversation import conversation_turn
    original = workflow.prepare_workflow
    changed = False
    def prepare(*args, **kwargs):
        nonlocal changed
        result = original(*args, **kwargs)
        if not changed:
            changed = True
            conversation_turn(TurnRequest(action='turn', conversation_id=CHAT, expected_revision=1,
                message='Explain the workflow without making a new proposal.'), project_root=project,
                model_client=Client({'message': 'Explanation only.', 'plan': None}))
        return result
    monkeypatch.setattr(workflow, 'prepare_workflow', prepare)
    with pytest.raises(InterfaceApiError, match='Conversation changed'):
        submission_action(request(), project_root=project, model_client=Client(), background=False)
    assert receipt(project)['run'] is None
    assert not list((project / 'workflow-state/interface-runs').glob('*.json'))


@pytest.mark.parametrize('extension,skill', [('geojson','inspect_vector'),('gpkg','inspect_vector'),('shp','inspect_vector'),('tif','inspect_raster')])
def test_spatial_submission_uses_bounded_worker_and_reconciles(project, extension, skill):
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    name = 'spatial.' + extension
    path = project / 'data/input' / name
    if skill == 'inspect_vector':
        frame = gpd.GeoDataFrame({'id':[1,2]}, geometry=gpd.points_from_xy([1,2],[3,4]), crs='EPSG:4326')
        frame.to_file(path, driver={'shp':'ESRI Shapefile','gpkg':'GPKG','geojson':'GeoJSON'}[extension])
    else:
        with rasterio.open(path, 'w', driver='GTiff', width=4, height=3, count=1, dtype='uint8', crs='EPSG:4326', transform=from_origin(1,4,1,1)) as dataset:
            dataset.write(np.ones((1,3,4),dtype='uint8'))
    before = {p.name:p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    message = f'Inspect {name}. Return CRS. No writes.'
    req = request()
    req.turn.message = message
    reply = {'message':'Ready','plan':{'summary':'Inspect spatial metadata','steps':[{'step_id':'step_1','skill':skill,'purpose':'Inspect metadata','arguments':{'path':name}}]}}
    client = Client(reply)
    result = submission_action(req, project_root=project, model_client=client, background=False)
    assert result['submission']['status'] == 'started'
    assert result['run']['status'] == 'completed', result['run']
    outcome = result['run']['steps'][0]['outcome']
    assert outcome['source'] == 'data/input/' + name
    if skill == 'inspect_vector':
        assert outcome['layers'][0]['feature_count'] == 2
        assert outcome['layers'][0]['crs'] == 'EPSG:4326'
    else:
        assert (outcome['width'],outcome['height'],outcome['band_count']) == (4,3,1)
        assert outcome['crs'] == 'EPSG:4326'
    assert result['approval_performed'] is False
    assert before == {p.name:p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    assert submission_action(req, project_root=project, model_client=client, background=False)['run']['run_id'] == result['run']['run_id']
    assert client.calls == 1
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    payload=project/'spatial-receipt.json'
    payload.write_text(SubmissionRequest(action='read',submission_id=SUBMISSION,conversation_id=CHAT).model_dump_json())
    cli=CliRunner().invoke(app,['planning-submit','--request-file',str(payload),'--project-root',str(project)])
    assert cli.exit_code == 0, cli.output
    assert json.loads(cli.stdout)['run']['run_id'] == result['run']['run_id']
    assert client.calls == 1


def test_spatial_sidecar_change_invalidates_source(project):
    import geopandas as gpd
    name='shape.shp'
    path=project/'data/input'/name
    gpd.GeoDataFrame({'id':[1]},geometry=gpd.points_from_xy([1],[2]),crs='EPSG:4326').to_file(path)
    req=request(); req.turn.message='Inspect shape.shp. Return CRS. No writes.'
    reply={'message':'Ready','plan':{'summary':'Inspect shape','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect','arguments':{'path':name}}]}}
    result=submission_action(req,project_root=project,model_client=Client(reply,hook=lambda:path.with_suffix('.prj').write_text('changed')),background=False)
    assert result['run']['status']=='failed'
    assert not result['run']['steps'][0]['outcome']


@pytest.mark.parametrize('name,content', [('bad.gpkg',b'<VRTDataset/>'),('bad.tif',b'<VRTDataset/>'),('bad.geojson',b'{"type":"FeatureCollection","features":[],"crs":{"type":"link","properties":{"href":"http://example.invalid"}}}')])
def test_external_or_disguised_spatial_sources_rejected(project,name,content):
    from geoagent_harness.interface_api.inspection_policy import bounded_read
    (project/'data/input'/name).write_bytes(content)
    with pytest.raises(InterfaceApiError,match='Bounded inspection failed'):
        bounded_read(project,action='snapshot',path='data/input/'+name)


def test_raster_sidecar_and_shapefile_symlink_rejected(project):
    from geoagent_harness.interface_api.spatial_inspection_snapshot import snapshot
    folder=project/'data/input'
    (folder/'local.tif').write_bytes(b'II*\x00')
    (folder/'local.tif.aux.xml').write_text('external')
    with pytest.raises(ValueError,match='sidecars'):
        snapshot(project,'data/input/local.tif')
    (folder/'linked.shp').write_bytes(b'\x00\x00\x27\x0a')
    (folder/'linked.shx').write_bytes(b'index')
    (folder/'linked.dbf').symlink_to(folder/'sample_orders.csv')
    with pytest.raises(ValueError,match='unsafe'):
        snapshot(project,'data/input/linked.shp')


def test_spatial_limits_reject_before_full_vector_read(project):
    from geoagent_harness.interface_api.spatial_inspection_snapshot import snapshot
    path=project/'data/input/large.geojson'
    path.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':None,'properties':{}}]*10001}))
    with pytest.raises(ValueError,match='feature limit'):
        snapshot(project,'data/input/large.geojson')


def test_raster_band_limit_records_failed_read_without_outputs(project):
    import rasterio
    from rasterio.transform import from_origin
    path=project/'data/input/many.tif'
    with rasterio.open(path,'w',driver='GTiff',width=1,height=1,count=17,dtype='uint8',transform=from_origin(1,4,1,1)):
        pass
    req=request();req.turn.message='Inspect many.tif. Return CRS. No writes.'
    reply={'message':'Ready','plan':{'summary':'Inspect raster','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect','arguments':{'path':'many.tif'}}]}}
    result=submission_action(req,project_root=project,model_client=Client(reply),background=False)
    assert result['run']['status']=='failed'
    assert not result['run']['steps'][0]['outcome']
    assert not (project/'data/output').exists()


def test_spatial_contract_binding_contains_adapter_version(project):
    from geoagent_harness.interface_api.inspection_policy import contract_digest, INSPECTION_CONTRACTS
    from unittest.mock import patch
    old=contract_digest(project,'inspect_vector')
    with patch.dict(INSPECTION_CONTRACTS['inspect_vector'],version='future'):
        assert contract_digest(project,'inspect_vector')!=old


@pytest.mark.parametrize('message,path', [
    ('Inspect terrain.tiff. Return CRS. No writes.','data/input/terrain.tiff'),
    ('Inspect terrain.tif. Return dimensions, bands, bounds and CRS. No writes.','data/input/terrain.tif'),
    ('Inspect parcels.shp. Return feature count, fields and CRS. No writes.','data/input/parcels.shp'),
])
def test_explicit_spatial_metadata_vocabulary(message,path):
    from geoagent_harness.interface_api.inspection_policy import request_source
    assert request_source(message)==path



def test_latest_inspection_source_is_bound_and_wrong_history_gets_one_correction(project):
    import copy
    first=request();first.turn.message='Inspect sample_points.geojson. Return CRS. No writes.'
    vector={'message':'Ready','plan':{'summary':'Inspect vector','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect','arguments':{'path':'sample_points.geojson'}}]}}
    a=submission_action(first,project_root=project,model_client=Client(vector),background=False)
    second=request();second.submission_id='e'*32;second.turn.expected_revision=a['conversation']['revision'];second.turn.message='Inspect sample_dem.tif. Return CRS. No writes.'
    wrong=copy.deepcopy(vector);wrong['plan']['steps'][0]['skill']='inspect_raster'
    good=copy.deepcopy(wrong);good['plan']['steps'][0]['arguments']['path']='sample_dem.tif'
    from tests.test_planner_conversation import Client as SequencedClient
    client=SequencedClient(wrong,good)
    b=submission_action(second,project_root=project,model_client=client,background=False)
    assert len(client.requests)==2
    assert b['run']['status']=='completed'
    assert b['run']['steps'][0]['outcome']['source']=='data/input/sample_dem.tif'
    assert len(b['conversation']['messages'])==4
    schema=client.requests[0].response_schema
    assert 'data/input/sample_dem.tif' in json.dumps(schema)
    assert a['run']['run_id']!=b['run']['run_id']


def test_repeated_wrong_inspection_source_does_not_replace_saved_plan(project):
    from tests.test_planner_conversation import Client as SequencedClient
    from geoagent_harness.planner.agent import PlannerAgentError
    first=submission_action(request(),project_root=project,model_client=Client(),background=False)
    bad={'message':'Ready','plan':{'summary':'Inspect TIFF','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect','arguments':{'path':'sample_orders.csv'}}]}}
    second=request();second.submission_id='e'*32;second.turn.expected_revision=1;second.turn.message='Inspect sample_dem.tif. Return CRS. No writes.'
    with pytest.raises(PlannerAgentError):submission_action(second,project_root=project,model_client=SequencedClient(bad,bad),background=False)
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    restored=conversation_turn(TurnRequest(action='read',conversation_id=CHAT),project_root=project)
    assert restored['planner_result']==first['conversation']['planner_result']
    assert len(list((project/'workflow-state/interface-runs').glob('*.json')))==1


def test_raster_to_csv_binds_latest_source_before_policy_and_storage(project):
    from tests.test_planner_conversation import Client as SequencedClient
    raster_reply={'message':'Ready','plan':{'summary':'Inspect raster','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect','arguments':{'path':'sample_dem.tif'}}]}}
    first=request();first.turn.message='Inspect sample_dem.tif. Return CRS. No writes.'
    prior=submission_action(first,project_root=project,model_client=Client(raster_reply),background=False)
    wrong=proposal();wrong['plan']['steps'][0]['arguments']['path']='sample_dem.tif'
    client=SequencedClient(wrong,proposal())
    second=request();second.submission_id='e'*32;second.turn.expected_revision=prior['conversation']['revision']
    response=submission_action(second,project_root=project,model_client=client,background=False)
    assert response['run']['status']=='completed'
    assert response['run']['steps'][0]['outcome']['source']=='data/input/sample_orders.csv'
    assert len(client.requests)==2
    args=client.requests[0].response_schema['$defs']['WorkflowPlan']['properties']['steps']['prefixItems'][0]['properties']['arguments']
    assert args['properties']['path']=={'type':'string','const':'data/input/sample_orders.csv'}
    assert 'latest inspection explicitly requests' in client.requests[1].messages[-1].content


def test_csv_format_error_identifies_step_operation_and_expected_formats():
    from geoagent_harness.planner.schemas import WorkflowPlan
    from geoagent_harness.planner.policy import validate_plan_policy, PlannerPolicyError
    reply=proposal();reply['plan']['steps'][0]['arguments']['path']='data/input/sample_dem.tif'
    with pytest.raises(PlannerPolicyError,match=r'step_1: inspect_csv requires .csv or .tsv input; path has format .tif'):
        validate_plan_policy(WorkflowPlan.model_validate(reply['plan']),available_skills={'inspect_csv'})
