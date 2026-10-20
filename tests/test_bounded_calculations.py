"""Known-answer, authority, interface/CLI parity and expression boundary checks."""
import hashlib
import json

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from tests.test_tabular_workflow import project, run, saved
from geoagent_harness.cli import app
from geoagent_harness.tabular.schemas import CalculateColumns
from geoagent_harness.tabular.service import run_operation, validate_output, TabularError
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.planner.schemas import PlannerResult


def column(name='amount'): return {'kind':'column','name':name}
def number(value): return {'kind':'number','value':value}
def binary(op,left,right): return {'kind':'binary','operator':op,'left':left,'right':right}
def arguments(expression=None, **extra):
    return {'path':'sample_orders.csv','target_path':'data/output/calculated.csv','missing_policy':'propagate',
            'calculations':[{'output_column':'doubled','expression':expression or binary('multiply',column(),number(2))}],**extra}
def proposal(args=None):
    return PlannerResult(model='fixture',original_request='Calculate twice amount; preserve missing values',context_references=[],plan={'summary':'Derived numeric amount','steps':[
        {'step_id':'step_1','skill':'calculate_csv_columns','purpose':'Double the original amount','arguments':args or arguments(),'requires_approval':True,'validation_required':True}]})


def test_calculation_full_workflow_and_independent_checks(project):
    result=run(project,proposal())
    assert result['status']=='validated_success'
    outcome=result['step_results'][0]['outcome']
    assert outcome['columns']==['order_id','region','amount','customer_id','unused','doubled']
    assert [row['doubled'] for row in outcome['preview']]==['20.0','40.0',None,'80.0','10.0','60.0']
    assert outcome['preview_truncated'] is False
    assert outcome['missing_counts']['doubled']==1
    assert result['step_results'][0]['validation_outcome']['checks']['calculation_values']
    assert outcome['calculation_arguments']['missing_policy']=='propagate'


def test_verifier_rejects_forged_values_even_with_updated_hash_and_metadata(project):
    outcome=run_operation('calculate_csv_columns',arguments(),load_settings())
    path=project/outcome['output']['path']
    data=path.read_bytes().replace(b'20.0',b'21.0')
    path.write_bytes(data)
    outcome['output']['sha256']=hashlib.sha256(data).hexdigest()
    assert not validate_output(outcome,load_settings())['checks']['calculation_values']


def test_conditional_is_lazy_and_missing_condition_propagates(project):
    (project/'data/input/numbers.csv').write_text('x,y\n10,2\n9,0\n,3\n')
    expression={'kind':'if','condition':{'kind':'compare','operator':'ne','left':column('y'),'right':number(0)},
                'then':binary('divide',column('x'),column('y')),'otherwise':number(0)}
    outcome=run_operation('calculate_csv_columns',arguments(expression,path='numbers.csv'),load_settings())
    assert [row['doubled'] for row in outcome['preview']]==['5.0','0.0',None]
    assert validate_output(outcome,load_settings())['passed']
    expression['condition']['left']=column('x')
    expression['then']=number(1)
    args=arguments(expression,path='numbers.csv',target_path='data/output/conditional.csv')
    outcome=run_operation('calculate_csv_columns',args,load_settings())
    assert outcome['preview'][-1]['doubled'] is None


@pytest.mark.parametrize('expression',[
    {'kind':'python','code':'import os'},
    binary('power',column(),number(2)),
    number(True),number('2'),number(float('inf')),
    {'kind':'compare','operator':'gt','left':column(),'right':number(1)},
    binary('add',{'kind':'compare','operator':'gt','left':column(),'right':number(1)},number(2)),
    {'kind':'if','condition':number(1),'then':number(1),'otherwise':number(0)},
])
def test_invalid_expression_rejected_without_writes(project,expression):
    with pytest.raises((ValidationError,ValueError)):
        saved(project,proposal(arguments(expression)))
    assert not list((project/'data/output').iterdir())


@pytest.mark.parametrize('change',['depth','nodes','bytes','columns','duplicate','no_policy','extra'])
def test_definition_limits(project,change):
    args=arguments()
    if change=='depth':
        expr=column()
        for _ in range(8):expr=binary('add',expr,number(1))
        args['calculations'][0]['expression']=expr
    elif change=='nodes':
        def tree(depth): return number(1) if depth==0 else binary('add',tree(depth-1),tree(depth-1))
        args['calculations']=[{'output_column':f'c{i}','expression':tree(4)} for i in range(4)]
    elif change=='bytes':
        def tree(depth):return column('x'*200) if depth==0 else binary('add',tree(depth-1),tree(depth-1))
        args['calculations'][0]['expression']=tree(5)
    elif change=='columns':args['calculations']*=6
    elif change=='duplicate':args['calculations']*=2
    elif change=='no_policy':args.pop('missing_policy')
    else:args['calculations'][0]['expression']['function']='eval'
    with pytest.raises(ValueError):CalculateColumns.model_validate(args)
    assert not list((project/'data/output').iterdir())


@pytest.mark.parametrize('change',['missing','unknown','collision','text','zero','overflow'])
def test_data_errors_reject_before_publication(project,change):
    args=arguments()
    if change=='missing':args['missing_policy']='error'
    elif change=='unknown':args['calculations'][0]['expression']=column('unknown')
    elif change=='collision':args['calculations'][0]['output_column']='amount'
    elif change=='text':args['calculations'][0]['expression']=column('region')
    elif change=='zero':args['calculations'][0]['expression']=binary('divide',column(),number(0))
    else:args['calculations'][0]['expression']=binary('multiply',number(1e308),number(1e308))
    with pytest.raises((TabularError,ValueError)):
        saved(project,proposal(args))
    assert not list((project/'data/output').iterdir())


def test_execution_rechecks_full_data_after_bounded_preflight(project):
    (project/'data/input/many.csv').write_text('x\n'+'1\n'*100+'0\n')
    args=arguments(binary('divide',number(1),column('x')),path='many.csv')
    saved(project,proposal(args))  # First 100 rows pass the read-only candidate check.
    with pytest.raises(TabularError,match='zero'):run_operation('calculate_csv_columns',args,load_settings())
    assert not list((project/'data/output').iterdir())


def test_cli_plan_and_execution_share_calculation_contract(project):
    runner=CliRunner();path=project/'calculation.json';path.write_text(proposal().plan.model_dump_json())
    result=runner.invoke(app,['workflow-plan',str(path),'--project-root',str(project)])
    assert result.exit_code==0,result.output
    payload=json.loads(result.output)
    filename=payload['saved']['plan_filename'];digest=payload['saved']['plan_sha256']
    review=runner.invoke(app,['workflow-review',filename,'--plan-sha',digest,'--project-root',str(project)])
    assert review.exit_code==0,review.output
    review_sha=json.loads(review.output)['review_sha256']
    blocked=runner.invoke(app,['workflow-execute',filename,'--plan-sha',digest,'--review-sha',review_sha,'--confirm-execution','--project-root',str(project)])
    assert blocked.exit_code!=0
    assert not list((project/'data/output').iterdir())
    authorization=runner.invoke(app,['workflow-authorize',filename,'--plan-sha',digest,'--review-sha',review_sha,'--approver','fixture','--reason','Temporary calculation','--project-root',str(project)])
    assert authorization.exit_code==0,authorization.output
    record=json.loads(authorization.output)
    executed=runner.invoke(app,['workflow-execute',filename,'--plan-sha',digest,'--review-sha',review_sha,'--confirm-execution','--plan-approval',record['plan_approval_filename'],'--recipe-approval',record['recipe_approval_filename'],'--project-root',str(project)])
    assert executed.exit_code==0,executed.output
    assert json.loads(executed.output)['status']=='validated_success'


def test_intermediate_calculation_and_retention(project):
    result=proposal();first=result.plan.steps[0]
    select=first.model_copy(deep=True,update={'skill':'select_csv_columns','arguments':{'path':'sample_orders.csv','columns':['order_id','amount'],'target_path':'data/output/selected.csv'}})
    first.step_id='step_2';first.arguments.pop('path');first.arguments['source_step']='step_1';first.depends_on=['step_1']
    result.plan.steps=[select,first]
    from tests.test_reusable_recipes_and_runs import execution
    from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
    outcome=run_action(RunRequest(action='start',workflow=execution(project,result)),project_root=project,background=False)
    assert outcome['status']=='completed'
    assert outcome['steps'][-1]['validation_outcome']['checks']['calculation_values']
    from geoagent_harness.recipe_catalog.successful import inventory
    assert inventory(project)


@pytest.mark.parametrize(('operator','expected'),[('add','8.0'),('subtract','4.0'),('multiply','12.0'),('divide','3.0')])
def test_arithmetic_known_answers(project,operator,expected):
    (project/'data/input/operands.csv').write_text('x,y\n6,2\n')
    outcome=run_operation('calculate_csv_columns',arguments(binary(operator,column('x'),column('y')),path='operands.csv',missing_policy='error'),load_settings())
    assert outcome['preview'][0]['doubled']==expected
    assert validate_output(outcome,load_settings())['passed']


@pytest.mark.parametrize(('operator','expected'),[('eq','0.0'),('ne','1.0'),('gt','1.0'),('ge','1.0'),('lt','0.0'),('le','0.0')])
def test_numeric_classification_known_answers(project,operator,expected):
    (project/'data/input/operands.csv').write_text('x,y\n6,2\n')
    expression={'kind':'if','condition':{'kind':'compare','operator':operator,'left':column('x'),'right':column('y')},'then':number(1),'otherwise':number(0)}
    outcome=run_operation('calculate_csv_columns',arguments(expression,path='operands.csv',missing_policy='error'),load_settings())
    assert outcome['preview'][0]['doubled']==expected
    assert validate_output(outcome,load_settings())['passed']
