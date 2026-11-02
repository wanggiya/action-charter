"""One isolated full-source inspection proposal, no operation dispatch or retries."""
import argparse,json,shutil,tempfile
from pathlib import Path
from geoagent_harness.model import SharedModelClient
from geoagent_harness.model.settings import ModelSettings
from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
from geoagent_harness.model.telemetry import read,error_code

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',default='qwen3.5:9b');parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--report',action='store_true')
    parser.add_argument('--reasoning',choices=['provider','none'],default='none');parser.add_argument('--max-tokens',type=int,default=1536)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='actioncharter-planning-diagnostics-') as directory:
        root=Path(directory)
        for name in ('context','agents'):shutil.copytree(repo/name,root/name)
        (root/'data/input/test').mkdir(parents=True)
        for name in ('diabetic_data.csv','IDS_mapping.csv'):shutil.copyfile(repo/'data/input/test'/name,root/'data/input/test'/name)
        client=SharedModelClient(ModelSettings(base_url='http://127.0.0.1:11434/v1',model=args.model,timeout_seconds=args.timeout,max_tokens=args.max_tokens,reasoning_effort=None if args.reasoning=='provider' else 'none'))
        request=TurnRequest(action='turn',conversation_id='a'*32,message='Inspect test/diabetic_data.csv, using test/IDS_mapping.csv for code definitions. Use the complete file, not a sample. Return row count, column names and numerical statistics for time_in_hospital. Treat identifiers as text and age as categorical bands. No writes.')
        if args.report:request=request.model_copy(update={'message':request.message+' Return a data-quality report in Outcome. No writes.'})
        try:
            response=conversation_turn(request,project_root=root,model_client=client)
            result={'status':'proposal_returned' if response.get('planner_result') else 'clarification','operation_ids':[s['skill'] for s in (response.get('planner_result') or {}).get('plan',{}).get('steps',[])]}
        except Exception as error:result={'status':'failed','error_code':error_code(error)}
        result.update(diagnostics=read(root,request.conversation_id),execution_performed=False,source_scope='temporary full-source copy',settings_scope='isolated model choice; launcher settings unchanged')
        with args.output.open('x') as stream:json.dump(result,stream,indent=2)
        print(json.dumps({k:v for k,v in result.items() if k!='diagnostics'}))

if __name__=='__main__':main()
