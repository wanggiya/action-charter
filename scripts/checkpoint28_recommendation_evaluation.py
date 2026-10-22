"""Frozen offline ranking evaluation. Synthetic evidence, no model or execution."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from time import perf_counter
from shutil import copytree
from geoagent_harness.planner.outcome_recommendations import record_outcome, recommendations, rank_recipes
from geoagent_harness.recipe_catalog.successful import contracts


def main():
    with TemporaryDirectory(prefix='actioncharter-ranking-') as directory:
        root=Path(directory);copytree(Path(__file__).resolve().parents[1]/'context',root/'context');scope='a'*32;current=contracts(root)
        def evidence(run,skill,passed):
            return {'run_id':f'{run:032x}','conversation_id':scope,'execution_performed':True,'finished_at':'2026-10-20',
                'status':'completed' if passed else 'validation_failed',
                'retention_basis':{'operations':[{'step_id':'step_1','skill_id':skill,'contract_sha256':current[skill]['contract_sha256']}]},
                'steps':[{'step_id':'step_1','skill_id':skill,'status':'validated_success' if passed else 'validation_failed','validation_outcome':{'passed':passed}}]}
        # Training evidence is separate from frozen choice cases. No text/data rows.
        for index in range(3):record_outcome(root,evidence(index+1,'inspect_csv',True))
        record_outcome(root,evidence(4,'filter_csv_rows',False))
        items=recommendations(root,scope,['inspect_csv','filter_csv_rows','inspect_vector'])
        def recipe(identity,name,skill):return SimpleNamespace(id=identity,name=name,description='',steps=[SimpleNamespace(skill=skill)])
        cases=[
            ('relevance_tie',{'csv'},[recipe('a','CSV workflow','filter_csv_rows'),recipe('b','CSV workflow','inspect_csv')],'b'),
            ('current_request_wins',{'vector'},[recipe('a','CSV workflow','inspect_csv'),recipe('b','vector workflow','inspect_vector')],'b'),
            ('no_history_baseline',{'vector'},[recipe('a','vector workflow','inspect_vector'),recipe('b','CSV workflow','inspect_csv')],'a')]
        results=[]
        for name,words,candidates,expected in cases:
            entry={'case':name,'expected':expected}
            for label,policy in [('baseline',[]),('evidence',items)]:
                start=perf_counter();choice=rank_recipes(candidates,words,policy)[0].id
                entry[label]={'choice':choice,'correct':choice==expected,'milliseconds':round((perf_counter()-start)*1000,4)}
            results.append(entry)
        isolation=recommendations(root,'c'*32,['inspect_csv'])==[]
        passed=all(r['evidence']['correct'] for r in results) and isolation
        report={'passed':passed,'scope':'offline synthetic selector only; not end-to-end model improvement',
                'policy':'own-chat-checks-v1','model_calls':0,'execution_calls':0,'interventions':0,
                'baseline_correct':sum(r['baseline']['correct'] for r in results),'evidence_correct':sum(r['evidence']['correct'] for r in results),
                'cases':results,'other_chat_isolated':isolation,'production_enablement':'optional OFF; no model-quality threshold established'}
        print(json.dumps(report,indent=2))
        if not passed:raise SystemExit(1)

if __name__=='__main__':main()
