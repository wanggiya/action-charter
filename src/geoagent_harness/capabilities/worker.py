"""Trusted finite interpreter tests. Reads one bounded JSON definition on stdin."""
from __future__ import annotations

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(10,11))
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_NPROC,(16,16))
    import sys,json
    raw=sys.stdin.buffer.read(64001)
    if len(raw)>64000:raise ValueError('Candidate exceeds bound')
    print(json.dumps(run(json.loads(raw)),separators=(',',':')))


def run(value):
    import csv,io,hashlib
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from importlib.metadata import version
    from geoagent_harness.operations.packages import parse_package,package_sha,ProjectionArguments
    from geoagent_harness.capabilities.text import execute_text,reference_value,verify_frame
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.tabular.service import read_frame
    p=parse_package(value)
    if p.adapter!='csv_text_transform' or version('pandas')!='3.0.5':raise ValueError('Unsupported adapter/runtime')
    def encoded(rows):
        out=io.StringIO();csv.writer(out,lineterminator='\n').writerows(rows);return out.getvalue()
    # Held-out inputs are owned by the worker, not submitted by Planner.
    samples=['  North  ','sOuTh','  multiple\t spaces\ninside  ','ß café','0007','NA',None,'__import__("os").system("false")','<b>literal</b>','', 'x'*200]
    column=p.text_transform.source_column;output=p.text_transform.output_column
    held=encoded([[column,'_acq_fixture_id'],*[[v,str(i)] for i,v in enumerate(samples)]])
    fixtures=[(f.csv,f.expected_csv,'declared') for f in p.tests]+[(held,None,'held_out')]
    results=[];negatives=[]
    for text,expected,kind in fixtures:
        with TemporaryDirectory(prefix='actioncharter-acquisition-test-') as directory:
            root=Path(directory);(root/'data/input').mkdir(parents=True)
            (root/'data/input/fixture.csv').write_text(text)
            settings=load_settings({}).model_copy(update={'project_root':root,'enable_write_tools':True,'allow_overwrite':False})
            args=ProjectionArguments(path='data/input/fixture.csv',target_path='data/output/result.csv',package_sha256=package_sha(p))
            before=hashlib.sha256((root/args.path).read_bytes()).hexdigest()
            result=execute_text(p.id,args,p.text_transform,settings)
            original=read_frame(text.encode());actual=read_frame((root/args.target_path).read_bytes())
            passed=verify_frame(original,actual,p.text_transform)
            if expected is not None:passed=passed and actual.equals(read_frame(expected.encode()))
            results.append({'kind':kind,'passed':passed,'row_count':len(actual),'columns':list(actual.columns)})
            if kind=='held_out':
                # Wrong values must fail independently, including original columns.
                wrong=actual.copy();wrong.loc[0,output]='acq_fixture_mismatch'
                negatives.append({'kind':'wrong_values_rejected','passed':not verify_frame(original,wrong,p.text_transform)})
                wrong=actual.copy();wrong.loc[0,column]='acq_original_mismatch'
                negatives.append({'kind':'original_mutation_rejected','passed':not verify_frame(original,wrong,p.text_transform)})
                cases=[('overwrite',args),('unsafe_output',args.model_copy(update={'target_path':'../escape.csv'})),('writes_off',args.model_copy(update={'target_path':'data/output/blocked.csv'}))]
                for name,attempt in cases:
                    try:execute_text(p.id,attempt,p.text_transform,settings.model_copy(update={'enable_write_tools':False}) if name=='writes_off' else settings)
                    except (ValueError,OSError):negatives.append({'kind':name,'passed':True})
                    else:negatives.append({'kind':name,'passed':False})
                negatives.append({'kind':'input_unchanged','passed':hashlib.sha256((root/args.path).read_bytes()).hexdigest()==before})
                negatives.append({'kind':'no_extra_outputs','passed':sorted(str(f.relative_to(root)) for f in root.rglob('*') if f.is_file())==['data/input/fixture.csv','data/output/result.csv']})
    return {'package_id':p.id,'package_sha256':package_sha(p),'passed':all(c['passed'] for c in results+negatives),
        'cases':results,'negative_cases':negatives,'runtime':'pandas==3.0.5','scope':'temporary_fixtures_only',
        'isolation':'closed_data_definition_in_resource_bounded_worker','arbitrary_python_executed':False,
        'limits':{'wall_seconds':20,'cpu_seconds':10,'address_space_bytes':2*1024**3,'file_bytes':1024**2,'open_files':64,'processes':16},
        'dependency_installed':False,'approval_performed':False,'execution_performed':False,'fixture_execution_performed':True}
