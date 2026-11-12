"""Exact analytical requests and refresh/reconciliation never replay failed work."""
import json
from pathlib import Path
from shutil import copytree

import pytest
from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
from geoagent_harness.platform.model_gateway.client import ModelClientError

PROMPT='Profile diabetic_data.csv using IDS_mapping.csv. Group by age, readmitted. Summarize time_in_hospital, number_inpatient. Count distinct patient_nbr, encounter_id. No writes.'
CHAT='a'*32


@pytest.fixture
def project(tmp_path):
    repo=Path(__file__).parents[1]
    for name in ['context','agents']:copytree(repo/name,tmp_path/name)
    (tmp_path/'README.md').write_text((repo/'README.md').read_text())
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/diabetic_data.csv').write_text('patient_nbr,encounter_id,age,readmitted,time_in_hospital,number_inpatient,admission_source_id\np1,e1,[50-60),NO,2,0,1\n')
    (tmp_path/'data/input/IDS_mapping.csv').write_text('admission_source_id,description\n1,Referral\n')
    return tmp_path


class NoModel:
    def complete(self,*args):raise AssertionError('Complete analytical profile must not call the model')


@pytest.mark.parametrize('entry',['conversation','submit_off','submit_on'])
def test_complete_profile_is_model_free_through_both_endpoints(project,entry):
    turn=TurnRequest(action='turn',conversation_id=CHAT,message=PROMPT)
    if entry=='conversation':
        response=conversation_turn(turn,project_root=project,model_client=NoModel())
    else:
        envelope=submission_action(SubmissionRequest(action='submit',submission_id='b'*32,
            conversation_id=CHAT,inspect_on_send=entry=='submit_on',turn=turn),project_root=project,model_client=NoModel(),background=False)
        response=envelope['conversation']
        assert envelope['run'] is None and not envelope['execution_performed']
    assert response['context_usage']['model_request']['model_calls']==0
    assert response['planner_result']['plan']['steps'][0]['arguments']['analysis']['numeric_columns']==['time_in_hospital','number_inpatient']
    assert not response['approval_performed'] and not response['execution_performed']
    assert not (project/'data/output').exists()


def test_timeout_and_receipt_refresh_preserve_last_plan_without_retry(project):
    saved=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,message=PROMPT),project_root=project,model_client=NoModel())
    class Timeout:
        calls=0
        def complete(self,request):
            self.calls+=1
            raise ModelClientError.timeout()
    client=Timeout()
    request=SubmissionRequest(action='submit',submission_id='c'*32,conversation_id=CHAT,turn=TurnRequest(
        action='turn',conversation_id=CHAT,expected_revision=1,message='Explain the current workflow and suggest what to explore next.'))
    with pytest.raises(ModelClientError):submission_action(request,project_root=project,model_client=client,background=False)
    assert client.calls==1
    for _ in range(2):
        receipt=submission_action(SubmissionRequest(action='read',submission_id='c'*32,conversation_id=CHAT),project_root=project,model_client=NoModel())
        restored=conversation_turn(TurnRequest(action='read',conversation_id=CHAT),project_root=project,model_client=NoModel())
        assert receipt['submission']['status']=='failed' and receipt['run'] is None
        assert receipt['conversation'] is None
        assert restored['planner_result']==saved['planner_result'] and restored['revision']==1
        assert not restored['execution_performed'] and not receipt['execution_performed']
    assert client.calls==1
