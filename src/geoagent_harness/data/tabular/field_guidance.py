"""Bounded, evidence-based advisory field selection; no statistics/authority inferred."""
import math
import re
import json
from collections import Counter

MARKERS={'?','NA','N/A','NULL','None','Unknown'}
IDENTIFIER=r'(^id$|_nbr$|^(?:patient|encounter)(?:_id|_number|_nbr)?$|identifier)'
CODE=r'(_id$|(^|_)code($|_)|^diag_|postal|zip)'
ROLES={'numerical','count','categorical','ordered_category','identifier','text','uncertain'}
INTERVAL=re.compile(r'\[\s*-?\d+(?:\.\d+)?\s*[-,]\s*-?\d+(?:\.\d+)?\s*[)\]]')


def classify_role(name,*,nonmarker,numeric,integer,minimum,bands,overflow,override=None,coded=False):
    """Same role rules for ordinary inspection and comprehensive profiling."""
    if override:return override,['explicit override'],'declared'
    if re.search(IDENTIFIER,name,re.I):return 'identifier',['identifier name hint'],'candidate'
    if re.search(CODE,name,re.I) or coded:return 'categorical',['coded field name or supplied codebook'],'candidate'
    if nonmarker and bands==nonmarker:return 'ordered_category',['all non-marker values are interval labels'],'candidate'
    if nonmarker and numeric/nonmarker>=.95:
        role='count' if re.search(r'number|count|visits|num_',name,re.I) and integer==numeric and (minimum or 0)>=0 else 'numerical'
        return role,['at least 95% numeric compatibility; semantic meaning remains a candidate'],'candidate'
    return ('categorical' if not overflow else 'uncertain'),['observed string/mixed values'],'candidate'


class GuidanceAccumulator:
    """One pass, fixed counters and at most 64 short distinct values per column."""
    def __init__(self,names,missing_values=None,coded_fields=()):
        self.missing=missing_values or {};self.coded=set(coded_fields);self.rows=0
        self.fields={name:{'missing':0,'markers':Counter(),'nonmarker':0,'numeric':0,'integer':0,'bands':0,'minimum':None,'maximum':None,'mean':0.,'m2':0.,'values':set(),'overflow':False} for name in names}
    def add(self,row):
        self.rows+=1
        for (name,p),value in zip(self.fields.items(),row):
            if value=='':p['missing']+=1;continue
            if value in MARKERS:p['markers'][value]+=1
            if value in self.missing.get(name,[]):p['missing']+=1;continue
            if not p['overflow']:
                if len(value)>160:p['overflow']=True;p['values'].clear()
                else:
                    p['values'].add(value)
                    if len(p['values'])>64:p['overflow']=True;p['values'].clear()
            if value in MARKERS:continue
            p['nonmarker']+=1
            if value.startswith('[') and INTERVAL.fullmatch(value):p['bands']+=1
            try:v=float(value)
            except ValueError:continue
            if not math.isfinite(v) or abs(v)>1e15:continue
            p['numeric']+=1;p['integer']+=v.is_integer()
            delta=v-p['mean'];p['mean']+=delta/p['numeric'];p['m2']+=delta*(v-p['mean'])
            p['minimum']=v if p['minimum'] is None else min(p['minimum'],v)
            p['maximum']=v if p['maximum'] is None else max(p['maximum'],v)
    def result(self,path,sha256):
        profiles=[]
        for name,p in self.fields.items():
            role,basis,confidence=classify_role(name,coded=name in self.coded,**{k:p[k] for k in ('nonmarker','numeric','integer','minimum','bands','overflow')})
            profiles.append({'name':name,'analytical_role':role,'classification_basis':basis,'classification_confidence':confidence,
                'observed_type':'integer_compatible' if p['numeric'] and p['integer']==p['numeric'] else 'number_compatible',
                'missing_count':p['missing'],'missing_tokens':self.missing.get(name,[]),'candidate_missing_markers':dict(p['markers']),'distinct_count':None if p['overflow'] else len(p['values']),
                'numeric':{'count':p['numeric'],'minimum':p['minimum'],'maximum':p['maximum'],'invalid_count':p['nonmarker']-p['numeric']}})
        return guidance_from_profiles(profiles,path=path,sha256=sha256,source_rows=self.rows,matching_rows=self.rows)


def guidance_from_profiles(profiles,*,path,sha256,source_rows,matching_rows):
    fields=[]
    for p in profiles:
        role=p['analytical_role'];numeric=p.get('numeric') or {};n=numeric.get('count',0)
        distinct=p.get('distinct_count');markers=sum(count for token,count in p.get('candidate_missing_markers',{}).items() if token not in p.get('missing_tokens',[]))
        caution=[]
        if p['missing_count']:caution.append(f"{p['missing_count']} declared/empty missing values")
        if markers:caution.append(f'{markers} potential missing-marker occurrences; definitions need review')
        if numeric.get('invalid_count',0):caution.append(f"{numeric['invalid_count']} incompatible numeric values")
        if not matching_rows:kind='review';suggestion='No matching observations; check the source/filter before selecting methods.'
        elif role=='identifier':kind='identifier';suggestion='Check distinct values and repeated entities; exclude from means/correlations and regression measurements.'
        elif role in {'numerical','count'} and n:
            if numeric.get('minimum')==numeric.get('maximum'):kind='review';suggestion='Constant observed numeric field; inspect frequencies/missingness rather than fit associations.'
            elif role=='numerical' and distinct is not None and distinct<=8 and matching_rows>=20 and p.get('observed_type')=='integer_compatible' and p['classification_confidence']!='declared':
                kind='review';suggestion='Few observed levels; confirm whether this is a code/category or a measurement before numerical statistics.'
            else:kind='measurement';suggestion='Candidate for mean, range, percentiles and spread; compare with other measurements only after checking units and joint complete rows.'
            if n<3:caution.append('Fewer than three valid numeric observations; association/inference is not established')
        elif role in {'categorical','ordered_category'} and distinct is not None and 1<distinct<=32:
            kind='grouping';suggestion='Candidate for counts, percentages and grouped comparisons; preserve codes/bands until their definitions are known.'
        else:kind='review';suggestion='Inspect field meaning, cardinality and missingness before choosing statistical methods.'
        fields.append({'name':p['name'],'role':role,'kind':kind,'basis':p['classification_basis'],'confidence':p['classification_confidence'],
            'numeric_count':n if numeric else None,'missing_count':p['missing_count'],'distinct_count':distinct,'suggestion':suggestion,'cautions':caution,
            'numeric_range_supported':bool(n and all(v is not None and abs(v)<=1e12 for v in (numeric.get('minimum'),numeric.get('maximum'))))})
    groups={kind:[f['name'] for f in fields if f['kind']==kind][:8] for kind in ('measurement','grouping','identifier','review')}
    priority=list(dict.fromkeys(name for names in groups.values() for name in names))
    selected=sorted(fields,key=lambda f:f['name'] not in priority)[:32]
    return {'schema_version':'field-guidance-v1','source':path,'source_sha256':sha256,'source_rows':source_rows,'matching_rows':matching_rows,
        'field_count':len(fields),'fields':selected,'omitted_fields':len(fields)-len(selected),'candidates':groups,
        'basis':'complete_verified_source' if matching_rows==source_rows else 'complete_matching_rows','advisory_only':True,
        'analysis_starters':analysis_starters(fields,source_rows=source_rows,matching_rows=matching_rows),
        'analysis_opportunities':analysis_opportunities(fields),
        'limitations':['Roles and method suggestions are candidates, not confirmed domain definitions. Numeric syntax does not establish measurement meaning.',
            'Potential marker strings are excluded from numeric-role compatibility counts, but source values and declared missing counts remain unchanged.',
            'Missing markers are not silently treated as missing; define the policy before statistical analysis.',
            'No outcome, regression design, causal relationship or execution permission is inferred. Choose the question and analysis unit first.',
            'Ordinary inspection retains at most 64 distinct short values per field; unavailable cardinality is not a sampled estimate.']}


def analysis_starters(fields,*,source_rows,matching_rows):
    """Small typed, unexecuted descriptive specs; never guess missingness or filters.

    Only complete numeric-compatible measurement candidates qualify. Grouping and
    domain interpretation remain explicit user/Planner choices. Filtered profiles
    need their original query, which this advisory contract does not retain.
    """
    if not 2<=matching_rows<=200000 or matching_rows!=source_rows:return []
    result=[]
    for field in fields:
        if field['kind']!='measurement' or field['numeric_count']!=matching_rows or field['missing_count'] or field['cautions'] or not field['numeric_range_supported']:continue
        # Keep the fixed profiling worker standard-library-only. The same typed
        # AnalysisOptions/StatisticsSpec validates these closed shapes at use.
        result.append({'column':field['name'],'analysis':{'statistics':{'methods':['describe'],'columns':[field['name']],'missing_policy':'error'}}})
        if len(result)==8:break
    return result


def analysis_opportunities(fields):
    """Registered method families and observed candidate fields, not a study design."""
    groups={kind:[f['name'] for f in fields if f['kind']==kind][:4] for kind in ('measurement','grouping','identifier','review')}
    options=[]
    def add(identity,title,names,contract,reason,requirements):
        options.append({'id':identity,'title':title,'fields':names,'operation':'inspect_csv','contract':contract,'reason':reason,'requirements':requirements})
    if groups['review']:
        add('quality','Resolve field meaning and missingness',groups['review'],'analysis.quality_columns / profile_columns',
            'Inspection flagged fields requiring review before selecting statistical methods.',
            ['Confirm code definitions and missing-marker meanings; do not silently convert or discard values.'])
    if groups['measurement']:
        add('distribution','Describe measurement distributions',groups['measurement'],'analysis.statistics.methods=[describe]',
            'Observed measurement candidates support checking range, percentiles and spread.',
            ['Confirm units and analysis unit; declare missingness policy.','Optional grouping must name an observed grouping field.'])
    if groups['grouping']:
        add('frequencies','Compare category counts and percentages',groups['grouping'],'analysis.group_by',
            'Observed category/band candidates can describe recorded row distributions.',
            ['Choose one or two grouping fields and state the percentage denominator.','Counts describe rows, not distinct people; preserve literal category labels.'])
    if groups['identifier']:
        add('entities','Check keys and repeated entities',groups['identifier'],'analysis.distinct_columns / duplicate_key',
            'Identifier candidates may distinguish row keys from entities observed repeatedly.',
            ['Count and verify uniqueness before claiming a key or repeated entities.','Choose an analysis unit before inference; IDs are not numerical predictors by default.'])
    return options


def compact_guidance(value):
    """Aggregate candidate field names only, no row values or secrets for agents."""
    result={k:value[k] for k in ('source','source_sha256','source_rows','matching_rows','field_count','candidates','advisory_only','limitations')}
    result['field_evidence']=[{k:f[k] for k in ('name','role','kind','numeric_count','missing_count','distinct_count','cautions')} for f in value['fields'][:16]]
    result['analysis_opportunities']=value.get('analysis_opportunities',[])
    if value.get('source_options') is not None:result['source_options']=value['source_options']
    return result


def bound_guidance(value,max_bytes):
    """Bound advisory presentation, never the source scan or observed counts."""
    while len(json.dumps(value,separators=(',',':'),allow_nan=False).encode())>max_bytes:
        if value['fields']:
            value['fields'].pop();value['omitted_fields']+=1
        elif value.get('analysis_opportunities'):
            value['analysis_opportunities'].pop()
        elif value.get('analysis_starters'):
            value['analysis_starters'].pop()
        else:
            groups=[names for names in value['candidates'].values() if names]
            if not groups:return None
            max(groups,key=len).pop()
    return value


def requests_field_guidance(message):
    return bool(re.match(r'^\s*(?:which|what|recommend|suggest|explain)\b',message,re.I)
        and (re.search(r'\b(?:fields?|columns?)\b',message,re.I) or re.search(r'\bnext\b',message,re.I))
        and re.search(r'\b(?:statistics|statistical|analys[ie]s|suggestions?)\b',message,re.I)
        and not re.search(r'\b(?:run|compute|calculate|fit|execute|write|export|install|delete|join|merge)\b',message,re.I))


def guidance_context(message,context):
    """Never substitute another source/hash when explaining recorded advice."""
    if not context:return None
    hashes=set(re.findall(r'\b[a-f0-9]{64}\b',message))
    names=set(re.findall(r'[\w.-]+\.(?:csv|tsv|xlsx|json|jsonl|ndjson)\b',message,re.I))
    candidates=[item for item in context['results'] if item.get('field_guidance')
        and (not hashes or item['field_guidance']['source_sha256'] in hashes)
        and (bool(hashes) or not names or item['field_guidance']['source'].rsplit('/',1)[-1] in names)]
    return {**context,'results':candidates} if candidates else None
