"""Standard-library comprehensive profiling, shared by local and sandbox runtimes."""
from array import array
from collections import Counter
import math
import os
import re
import sys
from geoagent_harness.discovery.csv import source,Reader,text_reader,records,header,row_values,identity,MAX_BYTES

from .field_guidance import MARKERS,IDENTIFIER,CODE,ROLES,classify_role,guidance_from_profiles

class Numeric:
    def __init__(self):self.n=0;self.mean=0.;self.m2=0.;self.minimum=None;self.maximum=None;self.total=0.;self.values=array('d');self.quantiles=True
    def add(self,v,collect=True):
        self.n+=1;delta=v-self.mean;self.mean+=delta/self.n;self.m2+=delta*(v-self.mean)
        self.minimum=v if self.minimum is None else min(self.minimum,v);self.maximum=v if self.maximum is None else max(self.maximum,v);self.total+=v
        if self.quantiles and collect:self.values.append(v)
        else:self.quantiles=False;self.values=array('d')
    def result(self):
        quantiles=None
        if self.n and self.quantiles:
            values=sorted(self.values)
            def quantile(p):
                index=(self.n-1)*p;i=int(index);return values[i]+(values[min(i+1,self.n-1)]-values[i])*(index-i)
            quantiles={'q1':quantile(.25),'median':quantile(.5),'q3':quantile(.75)}
        histogram=[]
        if self.n and self.quantiles:
            bins=Counter()
            for value in self.values:
                i=0 if self.maximum==self.minimum else min(11,int((value-self.minimum)/(self.maximum-self.minimum)*12))
                bins[i]+=1
            for i,count in sorted(bins.items()):
                lo=self.minimum+(self.maximum-self.minimum)*i/12;hi=self.minimum+(self.maximum-self.minimum)*(i+1)/12
                histogram.append({'label':f'{lo:.5g} – {hi:.5g}','count':count})
        return {'count':self.n,'mean':self.mean if self.n else None,'minimum':self.minimum,'maximum':self.maximum,'sum':self.total,
            'standard_deviation':math.sqrt(max(0,self.m2/(self.n-1))) if self.n>1 else None,
            'quantiles':quantiles,'quantile_status':'exact_linear_interpolation' if quantiles else 'unavailable_budget' if not self.quantiles else 'no_valid_values',
            'histogram':histogram,'histogram_status':'exact_12_equal_width_bins' if histogram else 'unavailable',
            'units':'unspecified'}


def inspect_dataset(root,path,options=None,*,delimiter=','):
    options=options or {};missing=options.get('missing_values',{});overrides=options.get('role_overrides',{})
    with source(root,path) as (fd,path,before):
        reader=Reader(fd,limit=MAX_BYTES);count=0;preview=[];quantile_entries=0
        with text_reader(reader) as text:
            parsed=records(text,delimiter);names=header(parsed)
            if (set(missing)|set(overrides))-set(names):raise ValueError('Profile policy references an absent field')
            book=read_codebook(root,options['codebook_path']) if options.get('codebook_path') else None
            page_columns=options.get('preview_columns') or names[:16]
            if set(page_columns)-set(names):raise ValueError('Preview references absent fields')
            page_offset=options.get('preview_offset',0);page_limit=options.get('preview_limit',20)
            columns={n:{'empty':0,'missing':0,'markers':Counter(),'values':Counter(),'overflow':False,'numeric':Numeric(),'invalid':0,'integer':0,'bands':0,'nonmarker':0,'mapped':0,'unmapped':0,'exact':Counter() if re.search(IDENTIFIER,n,re.I) or n in options.get('distinct_columns',[]) else None,'exact_failed':False,'state_bytes':0,'exact_bytes':0} for n in names}
            if any(role not in ROLES for role in overrides.values()):raise ValueError('Unknown analytical role override')
            state_bytes=0;groups={};group_entries=0
            group_by=options.get('group_by',[]);requested_numeric=options.get('numeric_columns',[]);requested_distinct=options.get('distinct_columns',[])
            if (set(group_by)|set(requested_numeric)|set(requested_distinct))-set(names):raise ValueError('Group query references absent fields')
            reserved={'row_count','proportion'}|{f'{n}_distinct' for n in requested_distinct}|{f'{n}_{m}' for n in requested_numeric for m in ['count','mean','sum','min','max']}
            if reserved.intersection(group_by):raise ValueError('Group names conflict with measures')
            filters=options.get('filters',[]);matched=0
            if any(f['column'] not in names for f in filters):raise ValueError('Filter references an absent column')
            for row in parsed:
                if not row:continue
                row_values(row,names);count+=1;values=dict(zip(names,row))
                if any(values[f['column']]!=f['value'] for f in filters):continue
                matched+=1;parsed_numeric={}
                if page_offset<matched<=page_offset+page_limit:preview.append({n:(values[n][:160] or None) for n in page_columns})
                for name,value in values.items():
                    p=columns[name];p['empty']+=value==''
                    if value in MARKERS:p['markers'][value]+=1
                    if value=='' or value in missing.get(name,[]):p['missing']+=1;continue
                    if not p['overflow']:
                        if value not in p['values']:
                            charge=sys.getsizeof(value)+80;p['state_bytes']+=charge;state_bytes+=charge
                        p['values'][value]+=1
                        if len(p['values'])>4096 or state_bytes>64*1024**2:
                            p['overflow']=True;p['values'].clear();state_bytes-=p['state_bytes'];p['state_bytes']=0
                    if p['exact'] is not None:
                        if value not in p['exact']:
                            charge=sys.getsizeof(value)+80;p['exact_bytes']+=charge;state_bytes+=charge
                        p['exact'][value]+=1
                        if len(p['exact'])>250000 or state_bytes>64*1024**2:
                            p['exact']=None;p['exact_failed']=True;state_bytes-=p['exact_bytes'];p['exact_bytes']=0
                    if book and name in book['sections']:
                        p['mapped' if value in book['sections'][name] else 'unmapped']+=1
                    if value in MARKERS:continue
                    p['nonmarker']+=1
                    if re.fullmatch(r'\[\s*-?\d+(?:\.\d+)?\s*[-,]\s*-?\d+(?:\.\d+)?\s*[)\]]',value):p['bands']+=1
                    try:v=float(value)
                    except ValueError:p['invalid']+=1;continue
                    if not math.isfinite(v) or abs(v)>1e15:p['invalid']+=1;continue
                    p['integer']+=v.is_integer()
                    parsed_numeric[name]=v
                    collect=overrides.get(name) in {'numerical','count'} or name not in overrides and not re.search(IDENTIFIER+'|'+CODE,name,re.I) and not (book and name in book['sections'])
                    if collect:quantile_entries+=1
                    p['numeric'].add(v,collect=collect and quantile_entries<=4000000)
                if group_by:
                    key=tuple(values[n] for n in group_by)
                    g=groups.setdefault(key,{'row_count':0,'numeric':{n:Numeric() for n in requested_numeric},'distinct':{n:set() for n in requested_distinct}})
                    if len(groups)>2000:raise ValueError('Group limit exceeds 2,000; refine grouping')
                    g['row_count']+=1
                    for n in requested_numeric:
                        if n in parsed_numeric:g['numeric'][n].add(parsed_numeric[n],collect=False)
                    for n,seen in g['distinct'].items():
                        v=values[n]
                        if v and v not in missing.get(n,[]) and v not in seen:
                            seen.add(v);group_entries+=1;state_bytes+=sys.getsizeof(v)+80
                            if state_bytes>64*1024**2:raise ValueError('Grouped distinct state exceeds 64 MiB')
                            if group_entries>250000:raise ValueError('Grouped distinct limit exceeded')
        if identity(os.fstat(fd))!=before or reader.bytes!=before[2]:raise ValueError('Source changed while profiling')
        with source(root,path) as (_,_,after):
            if after!=before:raise ValueError('Source path changed while profiling')
    profiles=[]
    for name,p in columns.items():
        n=p['numeric']
        role,basis,confidence=classify_role(name,nonmarker=p['nonmarker'],numeric=n.n,integer=p['integer'],minimum=n.minimum,bands=p['bands'],overflow=p['overflow'],override=overrides.get(name),coded=bool(book and name in book['sections']))
        observed='empty' if not p['nonmarker'] else 'interval_labels' if p['bands']==p['nonmarker'] else 'integer_compatible' if n.n==p['nonmarker'] and p['integer']==n.n else 'number_compatible' if n.n==p['nonmarker'] else 'mixed' if n.n else 'text'
        numeric=n.result() if role in {'numerical','count'} else None
        undeclared_markers=sum(v for k,v in p['markers'].items() if k not in missing.get(name,[]))
        if numeric:numeric['invalid_count']=p['invalid']+undeclared_markers
        frequencies=p['exact'] if p['exact'] is not None else None if p['exact_failed'] or p['overflow'] else p['values']
        categories=[{'value':v[:160],'count':c,'proportion':c/matched if matched else None,'description':book['sections'].get(name,{}).get(v) if book else None} for v,c in p['values'].most_common(12)] if not p['overflow'] and role!='identifier' else []
        profiles.append({'name':name,'observed_type':observed,'analytical_role':role,'classification_basis':basis,'classification_confidence':confidence,
            'missing_count':p['missing'],'empty_count':p['empty'],'declared_missing_count':p['missing']-p['empty'],
            'candidate_missing_markers':dict(p['markers']),'missing_tokens':missing.get(name,[]),'missing_proportion':p['missing']/matched if matched else None,
            'distinct_count':len(frequencies) if frequencies is not None else None,'distinct_status':'exact' if frequencies is not None else 'unavailable_budget',
            'frequency':None if frequencies is None else {'once_only_values':sum(c==1 for c in frequencies.values()),'repeated_values':sum(c>1 for c in frequencies.values())},
            'numeric':numeric,'numeric_status':'computed_valid_numeric_subset' if numeric and n.n else 'no_valid_values' if numeric else 'not_applicable',
            'categories':categories,'categories_status':'not_applicable_identifier' if role=='identifier' else 'unavailable_budget' if p['overflow'] else 'exact_counts_top_12'})
    group_rows=[]
    for key,g in sorted(groups.items()):
        r={**dict(zip(group_by,key)),'row_count':g['row_count'],'proportion':g['row_count']/matched}
        for n,v in g['numeric'].items():r.update({f'{n}_count':v.n,f'{n}_mean':v.mean if v.n else None,f'{n}_sum':v.total,f'{n}_min':v.minimum,f'{n}_max':v.maximum})
        for n,v in g['distinct'].items():r[n+'_distinct']=len(v)
        group_rows.append(r)
    if book:
        book['coverage']={name:{'matched_rows':columns[name]['mapped'],'unmatched_rows':columns[name]['unmapped']} for name in book['sections'] if name in columns}
        book['unbound_sections']=[name for name in book['sections'] if name not in columns]
        with source(root,book['path']) as (_,_,after):
            if after!=book['identity']:raise ValueError('Codebook changed during profile')
    return {'schema_version':'dataset-profile-v1','source':path,'source_sha256':reader.sha.hexdigest(),'source_rows':count,'matching_rows':matched,
        'field_guidance':guidance_from_profiles(profiles,path=path,sha256=reader.sha.hexdigest(),source_rows=count,matching_rows=matched),
        'scope':'complete_parsed_file','groups':group_rows,'group_by':group_by,'distinct_counts':{p['name']:p['distinct_count'] for p in profiles if p['name'] in requested_distinct and p['distinct_count'] is not None},'columns':names,'profiles':profiles,'codebook':book,
        'table':{'columns':page_columns,'preview':preview,'row_count':matched,'offset':page_offset,'limit':page_limit,'preview_truncated':len(preview)<matched or len(page_columns)<len(names)},
        'query':options,'checks':{'profile_count_matches_columns':len(profiles)==len(names),'complete_source_hashed':reader.bytes==before[2]},
        'limitations':['Analytical roles are candidates unless explicitly overridden; name hints are not clinical definitions.',
            'Candidate missing markers are reported, not silently reclassified. Numerical measures exclude nonnumeric values.',
            'Quantiles/histograms are exact only when their complete valid values fit the 4,000,000-value shared budget.',
            'Distinct counters are exact within 250,000 entries per identifier/requested field and the 64 MiB shared state budget; otherwise unavailable.']}


def read_codebook(root,path):
    sections={};current=None
    with source(root,path) as (fd,path,before):
        if before[2]>256*1024:raise ValueError('Codebook exceeds 256 KiB')
        reader=Reader(fd,limit=256*1024)
        with text_reader(reader) as text:
            for row in records(text,','):
                if not row or all(not v.strip() for v in row):current=None;continue
                if len(row)!=2 or any(len(v)>1000 for v in row):raise ValueError('Codebook requires bounded two-column sections')
                key,label=(v.strip() for v in row)
                if current is None:
                    if not key or label.casefold()!='description' or key in sections or len(sections)>=16:raise ValueError('Invalid codebook header')
                    current=key;sections[current]={}
                else:
                    if not key or not label or key in sections[current] or len(sections[current])>=256:raise ValueError('Invalid codebook codes')
                    sections[current][key]=label
        if identity(os.fstat(fd))!=before:raise ValueError('Codebook changed')
        with source(root,path) as (_,_,after):
            if after!=before:raise ValueError('Codebook path changed')
    return {'identity':before,'path':path,'sha256':reader.sha.hexdigest(),'sections':sections}
