"""Fixed JSON profile worker; intentionally standard-library only."""
import json,resource,sys
from pathlib import Path

def main():
    resource.setrlimit(resource.RLIMIT_CPU,(90,91))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    raw=sys.stdin.buffer.read(16385)
    if len(raw)>16384:raise ValueError('Job exceeds input limit')
    job=json.loads(raw)
    if set(job)!={'options','delimiter'}:raise ValueError('Unsupported worker job')
    options=job['options']
    if set(options)-{'codebook_path','missing_values','role_overrides','filters','group_by','numeric_columns','distinct_columns','preview_columns','preview_offset','preview_limit'}:raise ValueError('Unsupported profile options')
    if options.get('codebook_path') not in {None,'data/input/codebook.csv'}:raise ValueError('Unsupported codebook binding')
    from geoagent_harness.tabular.dataset_profile import inspect_dataset
    result=inspect_dataset(Path('/job'),'data/input/source.csv',options,delimiter=job['delimiter'])
    encoded=json.dumps(result,separators=(',',':'),allow_nan=False).encode()
    if len(encoded)>1024**2:raise ValueError('Result exceeds 1 MiB')
    sys.stdout.buffer.write(encoded)

if __name__=='__main__':main()
