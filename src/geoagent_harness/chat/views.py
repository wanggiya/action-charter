"""Pure projections/rendering of recorded profiles; no scans, models or writes."""
import json,re
from pathlib import PurePosixPath
from .client import ChatError
VIEWS={'overview','columns','table','chart','groups','checks'}

def cross_tab(groups,keys,matching,*,measure='count',swap=False):
    """Bound the displayed matrix, never its population or marginal totals."""
    if len(keys)!=2:return None
    if measure not in {'count','row','column','total'}:raise ChatError('Choose count, row, column or total')
    a,b=keys[::-1] if swap else keys
    row_values=list(dict.fromkeys(g[a] for g in groups));col_values=list(dict.fromkeys(g[b] for g in groups))
    counts={};rt={};ct={}
    for g in groups:
        x,y,n=g[a],g[b],g['row_count']
        counts[x,y]=counts.get((x,y),0)+n;rt[x]=rt.get(x,0)+n;ct[y]=ct.get(y,0)+n
    total=sum(rt.values())
    def value(n,row,col):
        if measure=='count':return n
        denominator=row if measure=='row' else col if measure=='column' else matching
        return f'{100*n/denominator:.2f}%' if denominator else 'N/A'
    def label(v):return '(missing)' if v is None else '(empty cell)' if v=='' else str(v)
    rows=[[label(x),*[value(counts.get((x,y),0),rt[x],ct[y]) for y in col_values[:12]],value(rt[x],rt[x],total)] for x in row_values[:25]]
    rows.append(['Total',*[value(ct[y],total,ct[y]) for y in col_values[:12]],value(total,total,total)])
    return {'headers':[a+' / '+b,*[label(y) for y in col_values[:12]],'Total'],'rows':rows,
        'measure':measure,'row_field':a,'column_field':b,'row_categories':len(row_values),'column_categories':len(col_values),
        'grouped_rows':total,'matching_rows':matching,'reconciles':total==matching}


def saved_view(state,view='overview',*,source=None,field=None,offset=0,limit=20,cross_measure='count',cross_swap=False):
    if view not in VIEWS:raise ChatError('Unknown view; choose overview, columns, table, chart, groups or checks')
    if offset<0 or not 1<=limit<=100:raise ChatError('Use offset >= 0 and limit 1–100')
    session=state.get('analytical_session') or {}
    profiles=[o['result']['dataset_profile'] for o in session.get('observations',[]) if isinstance(o.get('result',{}).get('dataset_profile'),dict)]
    profiles=[p for p in profiles if p.get('schema_version')=='dataset-profile-v1']
    if source:
        profiles=[p for p in profiles if p['source']==source or PurePosixPath(p['source']).name==source]
    if not profiles:raise ChatError('No matching comprehensive profile in this chat. Use chat show for older evidence or send an explicit exploration request.')
    if len(profiles)>1:raise ChatError('Choose --source from: '+', '.join(p['source'] for p in profiles))
    r=profiles[0]
    result={'chat_id':state['conversation_id'],'revision':state['revision'],'analysis_revision':session.get('conversation_revision'),
        'view':view,'source':r['source'],'source_sha256':r['source_sha256'],'source_rows':r['source_rows'],
        'matching_rows':r['matching_rows'],'scope':r['scope'],'recorded_only':True,'execution_performed':False}
    columns=r['profiles']
    if field:
        columns=[p for p in columns if p['name']==field]
        if not columns:raise ChatError('Field is absent from this recorded profile')
    if view=='overview':
        result.update(summary=session.get('message'),field_count=len(r['columns']),roles={role:sum(p['analytical_role']==role for p in r['profiles']) for role in sorted({p['analytical_role'] for p in r['profiles']})},runtime=r['runtime'].get('mode'),limitations=r['limitations'])
    elif view=='columns':result.update(total=len(columns),offset=offset,profiles=columns[offset:offset+limit])
    elif view in {'table','groups'}:
        if view=='groups':result['group_by']=r.get('group_by',[])
        rows=r['table']['preview'] if view=='table' else r['groups']
        if view=='groups' and r.get('group_by'):
            from geoagent_harness.tabular.dataset_views import percentages
            rows=[{**row,**percentage} for row,percentage in zip(rows,percentages(rows,r['group_by'],r['matching_rows']))]
        if view=='groups':result['cross_tab']=cross_tab(rows,r.get('group_by',[]),r['matching_rows'],measure=cross_measure,swap=cross_swap)
        result.update(columns=r['table']['columns'] if view=='table' else list(rows[0]) if rows else [],rows=rows[offset:offset+limit],offset=offset,loaded_rows=len(rows),total_rows=r['matching_rows'] if view=='table' else len(rows),preview_only=view=='table')
    elif view=='chart':
        p=columns[0] if field else next((p for p in columns if (p.get('numeric') or {}).get('histogram') or p.get('categories')),columns[0])
        n=p.get('numeric') or {};buckets=n.get('histogram') or [{'label':str(c['value'])+(' · '+c['description'] if c.get('description') else ''),'count':c['count']} for c in p['categories']]
        result.update(field=p['name'],analytical_role=p['analytical_role'],buckets=buckets,distribution_status=n.get('histogram_status') if n.get('histogram') else p['categories_status'],note='Full matching-source histogram or top 12 category counts. Omitted categories are not extrapolated; identifiers may have no distribution.')
    else:result.update(checks=r['checks'],runtime=r['runtime'],artifact=r['artifact'],query=r['query'],limitations=r['limitations'])
    return result


def clean(value,width=120):
    # Data/header text is untrusted: never allow terminal control sequences.
    value=str(value).replace('\x1b','')
    value=re.sub(r'[\x00-\x1f\x7f-\x9f]',' ',value)
    return value if len(value)<=width else value[:width-1]+'…'


def number(v):
    return 'N/A' if v is None else f'{v:,.8g}' if isinstance(v,float) else f'{v:,}' if isinstance(v,int) else clean(v)


def table(headers,rows):
    rows=[[clean(number(v),44) for v in row] for row in rows]
    headers=[clean(h,44) for h in headers]
    widths=[max([len(h),*[len(r[i]) for r in rows]]) for i,h in enumerate(headers)]
    return '\n'.join([' | '.join(h.ljust(w) for h,w in zip(headers,widths)), '-+-'.join('-'*w for w in widths),*[' | '.join(v.ljust(w) for v,w in zip(row,widths)) for row in rows]])


def render_view(v):
    lines=[f"Chat {v['chat_id']} · revision {v['revision']} · {v['view'].title()}",clean(v['source']),f"Analysis revision: {v.get('analysis_revision') or 'not recorded'}; saved snapshot, not current file freshness",f"{v['source_rows']:,} source rows · {v['matching_rows']:,} matching rows · saved evidence; no calculation rerun"]
    view=v['view']
    if view=='overview':lines += [clean(v.get('summary') or '',4000),f"Fields: {v['field_count']} · Runtime: {v['runtime']}",table(['Role','Fields'],list(v['roles'].items()))]
    elif view=='columns':
        if len(v['profiles'])==1:
            p=v['profiles'][0];n=p.get('numeric') or {};q=n.get('quantiles') or {}
            lines += [table(['Measure','Recorded value'],list({'Field':p['name'],'Observed type':p['observed_type'],'Role':p['analytical_role'],'Classification confidence':p['classification_confidence'],'Missing':p['missing_count'],'Distinct':p['distinct_count'],'Distinct status':p['distinct_status'],'Numeric status':p['numeric_status'],'Valid numeric':n.get('count'),'Invalid numeric':n.get('invalid_count'),'Mean':n.get('mean'),'Minimum':n.get('minimum'),'Maximum':n.get('maximum'),'Standard deviation':n.get('standard_deviation'),'Q1':q.get('q1'),'Median':q.get('median'),'Q3':q.get('q3'),'Quantile status':n.get('quantile_status'),'Candidate missing markers':json.dumps(p['candidate_missing_markers'])}.items()))]
        else:lines += [table(['Field','Type','Role','Missing','Distinct','Mean','Min','Max'],[[p['name'],p['observed_type'],p['analytical_role'],p['missing_count'],p['distinct_count'],(p.get('numeric') or {}).get('mean'),(p.get('numeric') or {}).get('minimum'),(p.get('numeric') or {}).get('maximum')] for p in v['profiles']])]
        if len(v['profiles'])==1:
            p=v['profiles'][0]
            if p['categories']:
                lines += ['Recorded value frequencies · full matching source',table(['Value / band','Rows','% matching rows'],[[c['value'],c['count'],f"{100*c['count']/v['matching_rows']:.2f}%" if v['matching_rows'] else 'N/A'] for c in p['categories']]),'Top recorded categories only; omitted values are not extrapolated.']
        lines += [f"Showing {len(v['profiles'])} of {v['total']} fields · offset {v['offset']}. N/A means unavailable/not applicable; inspect a field's statuses."]
    elif view in {'table','groups'}:
        if view=='groups' and v.get('cross_tab'):
            c=v['cross_tab']
            lines += [f"Cross-tab · {c['row_field']} × {c['column_field']} · {c['measure']}",table(c['headers'],c['rows']),
                f"{c['grouped_rows']:,} grouped / {c['matching_rows']:,} matching records. Totals include all categories.",
                f"Showing up to 25 / {c['row_categories']} row categories and 12 / {c['column_categories']} column categories. Use frontend category pages for the rest.",
                'Counts are records, not distinct patients. Missing-marker groups retained. Unobserved combinations: 0; undefined percentages: N/A.',
                'Percentage bases: row = its complete row; column = its complete column; total = all matching records. /crosstab count|row|column|total [swap] changes display only.']
            if not c['reconciles']:lines.append('WARNING: recorded group counts do not reconcile with matching rows.')
            return '\n'.join(lines)
        rows=v['rows'];headers=v['columns']
        if view=='groups' and v.get('group_by'):
            keys=v['group_by'];headers=keys+['Rows','% all matching rows','% within '+keys[0]]
            rows=[{**{k:r[k] for k in keys},'Rows':r['row_count'],'% all matching rows':f"{r['percentage_total']:.2f}%",'% within '+keys[0]:f"{r['percentage_within_primary']:.2f}%"} for r in rows]
            lines += ['Percentages use rows, not distinct patients; missing-marker groups are retained.']
        lines += [table(headers,[[r.get(c) for c in headers] for r in rows]) if headers else 'No groups were requested.',f"Showing {len(rows)} / {v['loaded_rows']} loaded rows · {v['total_rows']} recorded rows · offset {v['offset']}."]
        if v.get('source_offset') is not None:lines += [f"Matching-source row offset: {v['source_offset']}"]
        if v['preview_only']:lines += ['Bounded row preview only. Statistics in Columns/Chart cover the complete matching source.']
    elif view=='chart':
        lines += [clean(v['field'])+' · '+v['distribution_status']]
        lines += render_bars(v['buckets'],percentage=v.get('chart_unit')=='percentage',denominator=v['matching_rows']).splitlines()
        lines += [v['note']]
    else:
        lines += [table(['Check','Result'],[(k,'Passed' if b else 'Failed') for k,b in v['checks'].items()]),'SHA-256: '+v['source_sha256'],table(['Runtime property','Recorded value'],list(v['runtime'].items())),'Artifact: '+clean(json.dumps(v['artifact']),1000),'Query: '+clean(json.dumps(v['query']),2000)]
    if view in {'overview','checks'}:lines += [clean(s,500) for s in v.get('limitations',[])]
    return '\n'.join(lines)


def render_chat(state):
    lines=[f"Chat {state['conversation_id']} · revision {state['revision']}"]
    for m in state.get('messages',[]):lines += ['\n'+m['role'].title()+':',clean(m['content'],8000)]
    plan=state.get('planner_result')
    if plan:lines += ['\nSaved workflow proposal:',clean(plan['plan']['summary'],1000),*['  '+clean(s['step_id']+' · '+s['skill']) for s in plan['plan']['steps']]]
    if state.get('analytical_session'):lines += ['\nAnalytical results available: chat result '+state['conversation_id']]
    return '\n'.join(lines)


def interactive_view(client,state,view,*,source=None,field=None,offset=0,limit=20,cross_measure='count',cross_swap=False):
    """Restore the shared last interactive view; fallback to the original profile."""
    value=saved_view(state,view,source=source,field=field,offset=offset,limit=limit,cross_measure=cross_measure,cross_swap=cross_swap)
    if view not in {'table','groups'}:return value
    check=saved_view(state,'checks',source=source)
    response=client.post('/api/v1/analysis/view',{'action':'read','conversation_id':state['conversation_id'],
        'expected_revision':state['revision'],'source_sha256':check['source_sha256'],'profile_sha256':check['artifact']['sha256'],'view':view})
    r=response.get('result')
    if not r:return value
    if r['conversation_id']!=state['conversation_id'] or r['source_sha256']!=check['source_sha256'] or r['profile_sha256']!=check['artifact']['sha256']:raise ChatError('Saved view scope mismatch')
    rows=r['groups'] if view=='groups' else r['table']['preview']
    if view=='groups':value['cross_tab']=cross_tab(rows,r['group_by'],r['matching_rows'],measure=cross_measure,swap=cross_swap)
    value.update(matching_rows=r['matching_rows'],source_rows=r['source_rows'],rows=rows[offset:offset+limit],columns=list(rows[0]) if rows and view=='groups' else r['table']['columns'] if view=='table' else [],
        loaded_rows=len(rows),total_rows=len(rows) if view=='groups' else r['matching_rows'],group_by=r['group_by'],query=r['query'],interactive_selection=True,source_offset=r['table'].get('offset',0) if view=='table' else None)
    return value


def render_bars(buckets,*,percentage=False,denominator=None):
    peak=max([b['count'] for b in buckets],default=0)
    lines=['Value / group               Distribution               '+('Percentage' if percentage else 'Rows / % matching')]
    for b in buckets:
        value=b['count'];bar='#'*round(24*value/peak) if peak else ''
        annotation=(f"{value:.2f}%" if percentage else f"{number(value)}"+(f" / {100*value/denominator:.2f}%" if denominator else ''))
        lines.append(f"{clean(b['label'],26):26} {bar:24} {annotation}")
    if not buckets:lines.append('No bounded distribution available.')
    return '\n'.join(lines)


def grouped_chart(value,basis='total'):
    if basis not in {'total','within'}:raise ChatError('Use /chart groups total or /chart groups within')
    keys=value.get('group_by') or []
    if not keys or not value.get('rows'):raise ChatError('No saved grouping. Use /groups age or /groups age readmitted first.')
    if value['total_rows']>100:raise ChatError('More than 100 groups; use the group table or refine grouping. No groups silently omitted.')
    rows=value['rows']
    if 'percentage_total' not in rows[0]:
        from geoagent_harness.tabular.dataset_views import percentages
        rows=percentages(rows,keys,value['matching_rows'])
    field='percentage_within_primary' if basis=='within' else 'percentage_total'
    return {**value,'view':'chart','field':' / '.join(keys),'chart_unit':'percentage','distribution_status':'exact recorded groups',
        'buckets':[{'label':' · '.join(str(g[k]) or '(empty)' for k in keys),'count':g[field]} for g in rows],
        'note':('Percentage within each '+keys[0]+' group; separate denominators.' if basis=='within' else 'Percentage of all matching rows; one common denominator.')+' Row counts, not distinct patients. Saved evidence; no model call or rescan.'}
