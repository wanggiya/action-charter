"""Static discovery, typed package boundaries and shared CLI/interface execution."""
import json
from pathlib import Path
from shutil import copytree,copyfile
from types import SimpleNamespace
import pytest
from typer.testing import CliRunner
from geoagent_harness.cli import app
from geoagent_harness.operations.discovery import ScanRequest,scan_libraries,library_inventory
from geoagent_harness.operations.storage import save_scan,read_scan,candidate_page
from geoagent_harness.operations.packages import parse_package,test_package as package_test,install_package,installed_packages,package_sha,PackageError
from geoagent_harness.operations.registry import operation_catalog,argument_models
from geoagent_harness.skill_registry import load_skill_registry
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import validate_edit,EditRequest,WorkflowRequest,prepare_workflow,authorize_workflow,execute_workflow
from geoagent_harness.planner.schemas import PlannerResult

REPO=Path(__file__).parents[1]
MANIFEST=json.loads((REPO/'examples/checkpoint25/order_identity.operation.json').read_text())

class Distribution:
    def __init__(self,root,name='fixture',files=None):
        self.root=root;self.metadata={'Name':name};self.version='1.0.0';self.files=files or []
    def locate_file(self,file):return self.root/str(file)

@pytest.fixture
def project(tmp_path,monkeypatch):
    for name in ('context','agents'):copytree(REPO/name,tmp_path/name)
    (tmp_path/'data/input').mkdir(parents=True)
    for name in ('sample_orders.csv','sample_regions.csv','sample_points.geojson'):copyfile(REPO/'data/input'/name,tmp_path/'data/input'/name)
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('ENABLE_WRITE_TOOLS','true');monkeypatch.setenv('ALLOW_OVERWRITE','false')
    return tmp_path


def test_static_inventory_never_imports_or_runs_decorators_and_reports_types(tmp_path):
    (tmp_path/'module.py').write_text("""raise RuntimeError('IMPORT MUST NEVER RUN')
def normalize(value: str, *, token='secret-value') -> str:
    '''A typed declaration.'''
    return value
class Example:
    def method(self, count: int = 2): return count
    @property
    def rows(self): return []
def _private(): pass
""")
    distribution=Distribution(tmp_path,files=['module.py','native.so'])
    report=scan_libraries(ScanRequest(),[distribution])
    assert not report['imports_performed'] and not report['execution_performed']
    candidates={c['qualified_name']:c for c in report['candidates']}
    assert 'module._private' not in candidates
    assert candidates['module.normalize']['parameters'][0]['annotation']=='str'
    assert candidates['module.normalize']['parameters'][1]['default']=='[redacted]'
    assert candidates['module.Example.rows']['kind']=='property'
    assert all(not c['executable'] for c in report['candidates'])
    assert report['coverage'][0]['native_files']==1 and not report['coverage'][0]['complete']
    private=scan_libraries(ScanRequest(include_private=True),[distribution])
    assert any(c['qualified_name']=='module._private' for c in private['candidates'])


def test_discovery_bounds_symlinks_search_and_snapshot_identity(tmp_path,monkeypatch):
    import geoagent_harness.operations.discovery as discovery
    (tmp_path/'ok.py').write_text('def first(): pass\ndef second(): pass\n')
    (tmp_path/'outside.py').symlink_to('/etc/passwd')
    distribution=Distribution(tmp_path,files=['ok.py','outside.py'])
    report=scan_libraries(ScanRequest(),[distribution])
    assert report['candidate_count']==2 and report['coverage'][0]['skipped_files']==1
    digest=save_scan(tmp_path,report)
    restored=read_scan(tmp_path,digest)
    assert candidate_page(restored,'first')['match_count']==1
    assert candidate_page(restored,'',offset=0,limit=1)['next_offset']==1
    path=tmp_path/'library-discovery'/f'{digest}.json'
    path.write_text(path.read_text().replace('first','changed'))
    with pytest.raises(ValueError,match='identity'):read_scan(tmp_path,digest)
    monkeypatch.setattr(discovery,'MAX_CANDIDATES',1)
    bounded=scan_libraries(ScanRequest(),[distribution])
    assert bounded['truncated'] and bounded['candidate_count']==1
    with pytest.raises(ValueError):scan_libraries(ScanRequest(distributions=['missing']),[distribution])
    with pytest.raises(ValueError):candidate_page(report,limit=101)


def test_snapshot_directory_link_is_rejected(tmp_path):
    (tmp_path/'module.py').write_text('def identity(x): return x')
    report=scan_libraries(ScanRequest(),[Distribution(tmp_path,files=['module.py'])])
    target=tmp_path/'other';target.mkdir();(tmp_path/'library-discovery').symlink_to(target)
    with pytest.raises(OSError):save_scan(tmp_path,report)
    assert not list(target.iterdir())


def install(root):
    report=package_test(MANIFEST)
    assert report['passed'] and not report['execution_performed'] and report['fixture_execution_performed']
    installed=install_package(MANIFEST,report['package_sha256'],root=root,confirm=True)
    assert not installed['approval_performed'] and not installed['execution_performed']
    return report['package_sha256']


def proposal(digest):
    return PlannerResult(model='fixture',original_request='Use the installed order identity adapter and export',context_references=[],plan={'summary':'Installed CSV adapter example','steps':[
      {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect original','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
      {'step_id':'step_2','skill':'ext_order_identity','purpose':'Extract fixed columns','arguments':{'path':'data/input/sample_orders.csv','package_sha256':digest,'target_path':'data/output/identity.csv'},'requires_approval':True,'validation_required':True},
      {'step_id':'step_3','skill':'export_csv','purpose':'Export validated intermediate','arguments':{'source_step':'step_2','target_path':'data/output/final.csv'},'requires_approval':True,'validation_required':True}
    ]})


def stored(root,result):
    validated=validate_edit(EditRequest(action='validate_plan_edit',planner_result=result),project_root=root)
    record=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,confirmed_plan_sha256=validated['plan_sha256'],allowed_skill_ids=validated['allowed_skill_ids']),project_root=root)
    return WorkflowRequest(action='prepare_workflow',plan_filename=record['plan_filename'],confirmed_plan_sha256=record['plan_sha256'])


def test_installation_is_separate_from_exact_workflow_authority_and_lineage(project):
    digest=install(project)
    assert len(load_skill_registry(project).implemented_skills())==25
    catalog=operation_catalog(project)
    extension=next(op for op in catalog['operations'] if op['id']=='ext_order_identity')
    assert extension['default_arguments']['package_sha256']==digest
    assert extension['outputs'][0]['contract']=='csv_artifact'
    assert extension['approval_required'] and extension['validation_required']
    request=stored(project,proposal(digest));review=prepare_workflow(request,project_root=project)
    assert review['steps'][1]['adapter_configuration']['columns']==['order_id','region']
    with pytest.raises(api.InterfaceApiError):execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}),project_root=project)
    assert not (project/'data/output').exists()
    authorization=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Only temporary CSV outputs'}),project_root=project)
    result=execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':authorization['plan_approval_filename'],'recipe_approval_filename':authorization['recipe_approval_filename']}),project_root=project)
    assert result['status']=='validated_success'
    assert result['step_results'][1]['outcome']['package_sha256']==digest
    assert result['step_results'][1]['outcome']['preview'][0]['order_id']=='001'
    evidence=json.loads(Path(result['evidence_path']).read_text())
    assert len(evidence['lineage'])==2
    assert (project/'data/output/final.csv').read_text().startswith('order_id,region\n001,north\n')


@pytest.mark.parametrize('change',['code','adapter','duplicate_columns','wrong_hash','bad_fixture'])
def test_invalid_package_contracts_and_failed_fixtures_cannot_install(project,change):
    value=json.loads(json.dumps(MANIFEST))
    if change=='code':value['entrypoint']='os:system'
    elif change=='adapter':value['adapter']='arbitrary_python'
    elif change=='duplicate_columns':value['columns']=['order_id','order_id']
    elif change=='bad_fixture':value['tests'][0]['expected_csv']='wrong\nvalue\n'
    try:digest=package_sha(parse_package(value))
    except ValueError:digest='0'*64
    if change=='wrong_hash':digest='0'*64
    with pytest.raises(ValueError):install_package(value,digest,root=project,confirm=True)
    assert not (project/'operation-packages').exists()


def test_package_pin_tampering_and_links_reject_before_workflow_creation(project):
    digest=install(project)
    wrong=proposal('0'*64)
    with pytest.raises(api.InterfaceApiError,match='digest'):stored(project,wrong)
    path=project/'operation-packages/ext_order_identity.json'
    document=json.loads(path.read_text());document['package']['columns']=['amount'];path.write_text(json.dumps(document))
    with pytest.raises(PackageError,match='digest'):installed_packages(project)
    path.unlink();path.symlink_to(project/'data/input/sample_orders.csv')
    with pytest.raises(PackageError):installed_packages(project)
    assert not (project/'data/output').exists()


def test_cli_and_interface_catalog_and_package_installer_share_services(project):
    runner=CliRunner()
    tested=runner.invoke(app,['test-operation-package',str(REPO/'examples/checkpoint25/order_identity.operation.json')]);assert tested.exit_code==0,tested.output
    sha=json.loads(tested.output)['package_sha256']
    denied=runner.invoke(app,['install-operation-package',str(REPO/'examples/checkpoint25/order_identity.operation.json'),'--package-sha',sha,'--project-root',str(project)])
    assert denied.exit_code==2
    installed=runner.invoke(app,['install-operation-package',str(REPO/'examples/checkpoint25/order_identity.operation.json'),'--package-sha',sha,'--confirm-install','--project-root',str(project)])
    assert installed.exit_code==0,installed.output
    command=runner.invoke(app,['operations','--project-root',str(project)]);assert command.exit_code==0,command.output
    assert json.loads(command.output)==operation_catalog(project)
    frontend=api.interface_planner_skill_catalog(project)
    assert next(s for s in frontend['skills'] if s['id']=='ext_order_identity')['package_sha256']==sha
    assert not (project/'data/output').exists()


def test_planner_can_propose_installed_adapter_with_bound_package_without_execution(project):
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.model.schemas import ModelResult
    digest=install(project)
    client=SimpleNamespace(complete=lambda request:ModelResult(model='fixture',content=json.dumps({'message':'Review installed adapter','plan':proposal(digest).plan.model_dump(mode='json')})))
    response=conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,message='Use the installed order identity adapter'),project_root=project,model_client=client)
    assert response['planner_result']['plan']['steps'][1]['skill']=='ext_order_identity'
    assert 'ext_order_identity' in response['supported_skill_ids']
    assert not response['approval_performed'] and not response['execution_performed']
    assert not (project/'data/output').exists()


def test_operations_http_scan_package_test_install_and_origin_are_separate(project,tmp_path,monkeypatch):
    from http.server import ThreadingHTTPServer
    from http.client import HTTPConnection
    from threading import Thread
    import geoagent_harness.operations.discovery as discovery
    source=project/'metadata-library';source.mkdir();(source/'safe.py').write_text('def transform(value: str) -> str: return value\n')
    fake=Distribution(source,files=['safe.py'])
    monkeypatch.setattr(discovery.metadata,'distributions',lambda:[fake])
    server=ThreadingHTTPServer(('127.0.0.1',0),api._handler(project));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    connection=HTTPConnection(*server.server_address)
    def request(path,body=None,origin='http://127.0.0.1:5173'):
        connection.request('POST' if body else 'GET',path,json.dumps(body) if body else None,{'Content-Type':'application/json','Origin':origin})
        response=connection.getresponse();value=json.loads(response.read());return response.status,value
    try:
        status,inventory=request('/api/v1/operations/libraries');assert status==200 and inventory['libraries'][0]['name']=='fixture'
        status,report=request('/api/v1/operations/scan',{'action':'scan_installed_libraries','distributions':['fixture']});assert status==200 and report['candidate_count']==1
        status,page=request('/api/v1/operations/candidates?scan='+report['scan_sha256']+'&q=transform');assert status==200 and not page['candidates'][0]['executable']
        status,test=request('/api/v1/operations/test-package',{'action':'test_operation_package','manifest':MANIFEST});assert status==200 and test['passed']
        assert not (project/'operation-packages').exists()
        status,blocked=request('/api/v1/operations/install-package',{'action':'install_operation_package','manifest':MANIFEST,'confirmed_package_sha256':test['package_sha256'],'confirm_install':True},origin='https://foreign.example');assert status==403
        status,installed=request('/api/v1/operations/install-package',{'action':'install_operation_package','manifest':MANIFEST,'confirmed_package_sha256':test['package_sha256'],'confirm_install':True});assert status==200 and not installed['execution_performed']
        status,catalog=request('/api/v1/operations/catalog');assert status==200 and any(op['id']=='ext_order_identity' for op in catalog['operations'])
        assert not (project/'data/output').exists()
    finally:connection.close();server.shutdown();server.server_close();thread.join(timeout=5)


def test_cli_installed_adapter_complete_review_authorization_and_execution(project):
    digest=install(project);runner=CliRunner();file=project/'adapter-plan.json';file.write_text(proposal(digest).plan.model_dump_json())
    planned=runner.invoke(app,['workflow-plan',str(file),'--project-root',str(project)]);assert planned.exit_code==0,planned.output
    record=json.loads(planned.output)['saved'];name=record['plan_filename'];sha=record['plan_sha256']
    reviewed=runner.invoke(app,['workflow-review',name,'--plan-sha',sha,'--project-root',str(project)]);assert reviewed.exit_code==0,reviewed.output
    review=json.loads(reviewed.output);base=[name,'--plan-sha',sha,'--review-sha',review['review_sha256'],'--project-root',str(project)]
    denied=runner.invoke(app,['workflow-execute',*base,'--confirm-execution']);assert denied.exit_code==2
    assert not (project/'data/output').exists()
    authorized=runner.invoke(app,['workflow-authorize',*base,'--approver','fixture','--reason','Exact temporary adapter scope']);assert authorized.exit_code==0,authorized.output
    approval=json.loads(authorized.output)
    result=runner.invoke(app,['workflow-execute',*base,'--confirm-execution','--plan-approval',approval['plan_approval_filename'],'--recipe-approval',approval['recipe_approval_filename']]);assert result.exit_code==0,result.output
    assert json.loads(result.output)['status']=='validated_success'
    assert (project/'data/output/final.csv').read_text().startswith('order_id,region\n001,north\n')


def test_saved_scan_inventory_survives_reopening_and_rejects_tampering(tmp_path):
    from geoagent_harness.operations.storage import saved_scans
    assert saved_scans(tmp_path)['scans'] == []
    (tmp_path/'module.py').write_text('def identity(x): return x')
    report = scan_libraries(ScanRequest(), [Distribution(tmp_path, files=['module.py'])])
    digest = save_scan(tmp_path, report)
    inventory = saved_scans(Path(str(tmp_path)))
    assert inventory['scans'][0]['scan_sha256'] == digest
    assert inventory['scans'][0]['coverage'][0]['distribution'] == 'fixture'
    assert 'candidates' not in inventory['scans'][0]
    assert not inventory['execution_performed'] and not inventory['approval_performed']
    path = tmp_path/'library-discovery'/f'{digest}.json'
    path.write_text(path.read_text().replace('identity', 'tampered'))
    with pytest.raises(ValueError, match='identity'):
        saved_scans(tmp_path)
