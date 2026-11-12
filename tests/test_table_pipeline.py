"""Repeatable contracts across unrelated inputs and thin public adapters."""
import csv
import hashlib
import json
import statistics
from copy import deepcopy
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from geoagent_harness.contracts.table_sources import BATCH_BYTES, BATCH_ROWS, TABLE_SUFFIXES, TableRow, TableBatch, row_batches, table_format_catalog
from geoagent_harness.contracts.analysis_options import TableSourceDescriptor
from geoagent_harness.data.tabular.analytical_service import profile_table
from geoagent_harness.data.tabular.inspection import TableInspection, inspect_table


@pytest.mark.parametrize('field,group,values',[
    ('amount','region',[1.5,2.5,4.5,7.5]),
    ('temperature','station',[-4,0,3,9]),
])
def test_one_pipeline_repeats_across_unrelated_tables_and_all_readers(tmp_path,monkeypatch,field,group,values):
    from openpyxl import Workbook
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    rows=[{'record_id':f'{i:03d}',field:value,group:'A' if i<2 else 'B'} for i,value in enumerate(values)]
    for suffix,delimiter in [('csv',','),('tsv','\t')]:
        with (folder/f'rows.{suffix}').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter=delimiter);writer.writeheader();writer.writerows(rows)
    (folder/'rows.json').write_text(json.dumps(rows))
    for suffix in ('jsonl','ndjson'):(folder/f'rows.{suffix}').write_text('\n'.join(json.dumps(r) for r in rows))
    book=Workbook();book.active.title='Data';book.active.append(list(rows[0]))
    for row in rows:book.active.append(list(row.values()))
    book.save(folder/'rows.xlsx')
    calls=[];original=TableInspection.add_batch
    def observe(self,batch):
        assert isinstance(batch,TableBatch);calls.append(self.format.id)
        return original(self,batch)
    monkeypatch.setattr(TableInspection,'add_batch',observe)
    spec={'statistics':{'columns':[field],'by':[group]},'distinct_columns':['record_id']}
    baseline=None
    for suffix in ('csv','tsv','json','jsonl','ndjson','xlsx'):
        path=f'rows.{suffix}';before=(folder/path).read_bytes()
        result=inspect_table(tmp_path,path,analysis=spec,delimiter='\t' if suffix=='tsv' else ',')
        descriptor=TableSourceDescriptor.model_validate(result['table_source'])
        assert descriptor.sha256==hashlib.sha256(before).hexdigest()
        assert descriptor.rows==4 and descriptor.table_schema.columns==list(rows[0])
        assert not descriptor.execution_authority and descriptor.analytical_view.schema_version=='table-string-view-v1'
        r=result['table_analysis']['statistics']
        assert r['descriptive'][0]['mean']==statistics.mean(values)
        assert r['descriptive'][0]['variance']==pytest.approx(statistics.variance(values))
        assert [g['descriptive'][0]['mean'] for g in r['grouped_descriptive']]==[statistics.mean(values[:2]),statistics.mean(values[2:])]
        facts=(r['descriptive'],r['grouped_descriptive'],result['table_analysis']['distinct_counts'])
        if baseline is None:baseline=facts
        else:assert facts==baseline
        assert result['preview'][0]['record_id']=='000'
        assert (folder/path).read_bytes()==before
        # Additive result metadata never enters the historical v1 reference digest.
        reference=result['table_reference']
        old_identity={k:reference[k] for k in ('sources','query','delimiter')}
        assert hashlib.sha256(json.dumps(old_identity,sort_keys=True).encode()).hexdigest()==reference['reference_id']
    assert len(calls)==6 and set(calls)=={'csv','tsv','json','jsonl','xlsx'}
    from geoagent_harness.task_actions import data_tools as tools
    from geoagent_harness.apps.cli.main import app
    settings=SimpleNamespace(project_root=tmp_path,input_root=folder)
    mcp=tools.profile_table('rows.json',spec,settings=settings)['table_analysis']['statistics']
    reply=CliRunner().invoke(app,['inspect-table','rows.xlsx','--options',json.dumps(spec),'--project-root',str(tmp_path)])
    assert reply.exit_code==0,reply.output
    cli=json.loads(reply.output)['table_analysis']['statistics']
    assert cli['descriptive']==mcp['descriptive']==baseline[0]
    assert cli['grouped_descriptive']==mcp['grouped_descriptive']==baseline[1]
    assert set(cli['descriptive'][0]['percentiles'])=={'0.0','25.0','50.0','75.0','100.0'}
    assert not (tmp_path/'data/output').exists()


def test_batches_are_lazy_bounded_ordered_and_check_cancellation():
    seen=[];checks=[]
    def reader():
        for i in range(1000):
            seen.append(i);yield TableRow((i,),(str(i),),('integer',))
    batches=row_batches(reader(),checkpoint=lambda:checks.append(True))
    first=next(batches)
    assert len(first.rows)==BATCH_ROWS and len(seen)==BATCH_ROWS+1
    rest=list(batches)
    assert [r.native[0] for batch in [first,*rest] for r in batch.rows]==list(range(1000))
    assert all(len(b.rows)<=BATCH_ROWS and b.analytical_bytes<=BATCH_BYTES for b in [first,*rest])
    assert len(checks)==len(rest)+1
    large=TableRow(tuple(['x'*4096]*100),tuple(['x'*4096]*100),tuple(['string']*100))
    assert len(list(row_batches([large,large])))==2
    with pytest.raises(ValueError):TableBatch(tuple([large,large]))
    with pytest.raises(ValueError):TableBatch(tuple([TableRow(('x',),('x',),('string',))]*(BATCH_ROWS+1)))
    def stop():raise RuntimeError('cancelled')
    with pytest.raises(RuntimeError,match='cancelled'):list(row_batches(reader(),checkpoint=stop))


def test_descriptor_preserves_native_facts_and_explicit_compatibility_view(tmp_path):
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    (folder/'values.json').write_text('[{"id":"001","flag":true,"v":null},{"id":"002","flag":false,"v":""}]')
    result=inspect_table(tmp_path,'values.json',analysis={})
    source=result['table_source'];schema=source['schema']
    assert schema['null_counts']=={'v':1} and schema['empty_string_counts']=={'v':1}
    types=schema['storage_types_overrides'].get('flag',schema['storage_types_default'])
    assert types==['boolean'] and result['preview'][0]['flag'] is True
    assert result['table_analysis']['profiles'][2]['missing_count']==2
    altered=deepcopy(source);altered['execution_authority']=True
    with pytest.raises(ValueError):TableSourceDescriptor.model_validate(altered)
    altered=deepcopy(source);altered['schema']['null_counts']['unknown']=1
    with pytest.raises(ValueError):TableSourceDescriptor.model_validate(altered)
    altered=deepcopy(source);altered['schema']['null_counts']['v']=3
    with pytest.raises(ValueError):TableSourceDescriptor.model_validate(altered)
    assert 'fields' not in source  # No unbounded duplicate per-field metadata rows.


def test_registry_cli_and_mcp_discovery_share_the_authoritative_reader_contract(tmp_path):
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.capabilities.registry.registry import operation_catalog, TableMetadata
    from geoagent_harness.task_actions import data_tools as tools
    from geoagent_harness.platform.internal_mcp.client import READ_ONLY_TOOL_ALLOWLIST
    from geoagent_harness.apps.mcp.server import create_mcp_server
    import asyncio
    # Use the real trusted registry packaged by the project, not an invented adapter catalog.
    repository=Path(__file__).parents[1];root=tmp_path/'project';root.mkdir()
    for name in ('context','agents'):shutil.copytree(repository/name,root/name)
    settings=SimpleNamespace(project_root=root)
    operation=operation_catalog(root,'xlsx')['operations'][0]
    assert operation['id']=='inspect_csv' and operation['supported_source_formats']==[s[1:] for s in TABLE_SUFFIXES]
    assert operation['table_source_contract']==table_format_catalog()
    assert tools.list_operation_contracts('xlsx',settings=settings)==operation_catalog(root,'xlsx')
    reply=CliRunner().invoke(app,['operations','--query','xlsx','--project-root',str(root)])
    assert reply.exit_code==0,reply.output
    assert json.loads(reply.output)['operations'][0]['table_source_contract']==table_format_catalog()
    assert 'list_operation_contracts' in READ_ONLY_TOOL_ALLOWLIST
    assert 'list_operation_contracts' in {tool.name for tool in asyncio.run(create_mcp_server().list_tools())}
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    (folder/'old.csv').write_text('id,x\n001,1\n002,3\n')
    result=inspect_table(tmp_path,'old.csv')
    assert TableMetadata.model_validate(result).table_source is not None
    legacy={k:v for k,v in result.items() if k!='table_source'}
    assert TableMetadata.model_validate(legacy).table_source is None
