"""Task relationships remain inspection-only, including denied/expired records."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.approvals.schemas import ApprovalRecord
from geoagent_harness.approvals.service import plan_sha256
from geoagent_harness.task_history import append_task_event
from geoagent_harness.task_history.relationships import inspect_task_relationships

class TaskRelationshipTests(unittest.TestCase):
    def test_recipe_approval_uses_current_policy_without_granting_authority(self):
        from geoagent_harness.recipes.schemas import WorkflowRecipe, RecipeApprovalRecord
        from geoagent_harness.recipes.digest import recipe_sha256
        from geoagent_harness.skill_registry import load_skill_registry
        registry=load_skill_registry(Path(__file__).resolve().parents[1])
        for mode in ["approved", "denied", "expired", "wrong_scope", "wrong_recipe"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project=Path(directory);root=project / "task-history"
                recipe=WorkflowRecipe(recipe_id="fixture",summary="Convert",original_request="Convert",steps=[{
                    "step_id":"step_1","skill_id":"convert_vector","depends_on":[],
                    "arguments":{"path":"data/input/sample_points.geojson","target_path":"data/output/fixture.gpkg"},"output_ids":["converted_vector"]}])
                digest=recipe_sha256(recipe)
                approval=RecipeApprovalRecord(approval_id="recipe-approval-20261002t000000z-12345678",recipe_sha256="a"*64 if mode=="wrong_recipe" else digest,
                    decision="denied" if mode=="denied" else "approved",step_ids=["step_2"] if mode=="wrong_scope" else ["step_1"],
                    approver="fixture",reason="Fixture",created_at=datetime(2026,10,2,tzinfo=timezone.utc),
                    expires_at=datetime(2026,10,2,0,1,tzinfo=timezone.utc) if mode=="expired" else None)
                append_task_event(root=root,task_id="task-approval",event_type="request",summary="Fixture")
                for path,record in [(f"workflow-recipes/fixture.{digest}.json",recipe),(f"approvals/{approval.approval_id}.json",approval)]:
                    target=project/path;target.parent.mkdir(exist_ok=True);raw=record.model_dump_json().encode();target.write_bytes(raw)
                    append_task_event(root=root,task_id="task-approval",event_type="artifact_reference",summary="Reference",artifact_path=path,artifact_sha256=hashlib.sha256(raw).hexdigest())
                result=inspect_task_relationships(root=root,task_id="task-approval",project_root=project,registry=registry,now=datetime(2026,10,2,1,tzinfo=timezone.utc))
                self.assertEqual(result["execution_approval_relationships"][0]["decision_verified_now"],mode=="approved")
                self.assertFalse(result["execution_authorized"])

    def test_outcome_matches_recipe_and_complete_embedded_result(self):
        from geoagent_harness.recipes.schemas import WorkflowRecipe
        from geoagent_harness.recipes.digest import recipe_sha256
        for mode in ["exact", "wrong_recipe", "wrong_skill", "wrong_evidence", "missing_evidence", "altered"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project=Path(directory); root=project / "task-history"
                recipe=WorkflowRecipe(recipe_id="fixture",summary="Inspect",original_request="Inspect",steps=[{
                    "step_id":"step_1","skill_id":"inspect_vector","depends_on":[],"arguments":{"path":"data/input/sample.geojson"},"output_ids":["source_metadata"]}])
                digest=recipe_sha256(recipe)
                skill="inspect_raster" if mode=="wrong_skill" else "inspect_vector"
                result={"recipe_id":"fixture","recipe_sha256":"a"*64 if mode=="wrong_recipe" else digest,
                    "approval_id":"recipe-approval-fixture","final_status":"validated_success","validation_performed":False,
                    "step_results":[{"step_id":"step_1","skill_id":skill,"status":"completed","validation_performed":False,
                    "execution":{"step_id":"step_1","skill_id":skill,"status":"completed","output_ids":["source_metadata"],"result":{},"validation_performed":False}}]}
                embedded=json.loads(json.dumps(result))
                if mode=="wrong_evidence":embedded["warnings"]=["different result"]
                evidence={"recipe_id":"fixture","recipe_sha256":result["recipe_sha256"],"approval_id":result["approval_id"],
                    "final_status":"validated_success","run_result":embedded,"recorded_at":"2026-10-02T00:00:00Z",
                    "artifacts":[{"artifact_id":"source","role":"input","path":"data/input/sample.geojson","sha256":"b"*64,"size_bytes":1}]}
                records=[(f"workflow-recipes/fixture.{digest}.json",recipe.model_dump(mode="json")),("recipe-runs/fixture.json",result)]
                if mode!="missing_evidence":records.append(("recipe-evidence/fixture.json",evidence))
                append_task_event(root=root,task_id="task-outcome",event_type="request",summary="Fixture")
                for path,data in records:
                    target=project/path;target.parent.mkdir(exist_ok=True);raw=json.dumps(data).encode();target.write_bytes(raw)
                    append_task_event(root=root,task_id="task-outcome",event_type="artifact_reference",summary="Reference",artifact_path=path,artifact_sha256=hashlib.sha256(raw).hexdigest())
                if mode=="altered":(project/"recipe-runs/fixture.json").write_bytes(b"{}")
                observed=inspect_task_relationships(root=root,task_id="task-outcome",project_root=project)
                self.assertFalse(observed["execution_authorized"])
                if mode=="altered":self.assertTrue(observed["findings"]);self.assertFalse(observed["outcome_relationships"])
                else:self.assertEqual(observed["outcome_relationships"][0]["relationship"],"exact_recorded_outcome" if mode=="exact" else "unlinked")

    def test_recipe_requires_complete_source_definition_not_just_id(self):
        from geoagent_harness.planner.recipe_definition import planner_recipe_definition
        from geoagent_harness.recipes.digest import recipe_sha256
        for mode in ["exact", "arguments", "request", "outputs", "altered", "missing_plan"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project=Path(directory); root=project / "task-history"
                result=PlannerResult(model="fixture",original_request="Convert fixture",context_references=[],plan={
                    "summary":"Convert fixture", "steps":[{"step_id":"step_1","skill":"convert_vector","purpose":"Convert",
                    "arguments":{"path":"data/input/sample_points.geojson","target_path":"data/output/fixture.gpkg"},
                    "requires_approval":True,"validation_required":True}]})
                digest=plan_sha256(result.plan)
                recipe=planner_recipe_definition(result,digest)
                if mode=="arguments":recipe.steps[0].arguments["target_path"]="data/output/other.gpkg"
                if mode=="request":recipe.original_request="Different request"
                if mode=="outputs":recipe.steps[0].output_ids=["other_output"]
                append_task_event(root=root,task_id="task-recipe",event_type="request",summary="Fixture")
                records=[(f"workflow-recipes/{recipe.recipe_id}.{recipe_sha256(recipe)}.json",recipe)]
                if mode!="missing_plan":records.insert(0,(f"plans/planner-plan.{digest}.json",result))
                for path,record in records:
                    target=project/path;target.parent.mkdir(exist_ok=True);raw=record.model_dump_json().encode();target.write_bytes(raw)
                    append_task_event(root=root,task_id="task-recipe",event_type="artifact_reference",summary="Reference",artifact_path=path,artifact_sha256=hashlib.sha256(raw).hexdigest())
                if mode=="altered":target.write_bytes(b"{}")
                observed=inspect_task_relationships(root=root,task_id="task-recipe",project_root=project)
                self.assertFalse(observed["execution_authorized"])
                if mode=="altered":self.assertTrue(observed["findings"]);self.assertFalse(observed["recipe_relationships"])
                else:self.assertEqual(observed["recipe_relationships"][0]["relationship"],"exact_definition" if mode=="exact" else "unlinked")

    def test_exact_denied_expired_wrong_scope_and_altered(self):
        for mode in ['approved', 'denied', 'expired', 'wrong_scope', 'altered', 'unlinked']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                root = project / 'task-history'
                plan = PlannerResult(model='fixture', original_request='Convert fixture', context_references=[], plan={
                    'summary':'Convert fixture', 'steps':[{'step_id':'step_1','skill':'convert_vector','purpose':'Convert',
                    'arguments':{},'requires_approval':True,'validation_required':True}]})
                digest = plan_sha256(plan.plan)
                approval = ApprovalRecord(approval_id='approval-20261001t120000z-12345678', plan_sha256=('a'*64 if mode=='unlinked' else digest),
                    decision='denied' if mode=='denied' else 'approved', step_ids=['step_2'] if mode=='wrong_scope' else ['step_1'],
                    approver='fixture', reason='Reviewed fixture', created_at=datetime(2026,10,1,12,tzinfo=timezone.utc),
                    expires_at=datetime(2026,10,1,12,1,tzinfo=timezone.utc) if mode=='expired' else None)
                append_task_event(root=root,task_id='task-fixture',event_type='request',summary='Fixture')
                for path,record in [(f'plans/planner-plan.{digest}.json',plan),(f'approvals/{approval.approval_id}.json',approval)]:
                    target=project/path;target.parent.mkdir(exist_ok=True);raw=record.model_dump_json().encode();target.write_bytes(raw)
                    append_task_event(root=root,task_id='task-fixture',event_type='artifact_reference',summary='Stored fixture',artifact_path=path,artifact_sha256=hashlib.sha256(raw).hexdigest())
                if mode=='altered':target.write_bytes(b'{}')
                result=inspect_task_relationships(root=root,task_id='task-fixture',project_root=project,now=datetime(2026,10,1,13,tzinfo=timezone.utc))
                self.assertFalse(result['execution_authorized'])
                self.assertFalse(result['execution_performed'])
                if mode=='altered':self.assertTrue(result['findings']);self.assertFalse(result['relationships'])
                else:self.assertEqual(result['relationships'][0]['decision_verified'],mode=='approved')
