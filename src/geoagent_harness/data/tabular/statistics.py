from geoagent_harness.contracts.statistics import StatisticsError, RegressionSpec, StatisticsSpec
"""Typed statistical methods over the existing hash-verified CSV scan.

No expressions, formula evaluation, generated code, dataset writes or model fitting
outside the declared numeric specification. Optional scientific imports are lazy.
"""
from array import array
from collections import Counter
import math
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator




class StatisticsAccumulator:
    def __init__(self,spec,names,missing_values):
        self.spec=spec;self.columns=spec.numeric_columns();self.missing_values=missing_values
        self.cluster=spec.regression.cluster_column if spec.regression else None
        if set(self.columns+spec.by+([self.cluster] if self.cluster else []))-set(names):raise StatisticsError('Statistical field is not present in the source')
        self.values=array('d');self.groups=array('q');self.cluster_ids={};self.matched=0;self.excluded=0
        self.group_ids={};self.group_rows=array('q');self.group_counts=Counter()
        self.missing={c:0 for c in self.columns};self.invalid={c:0 for c in self.columns};self.missing_clusters=0
    def add(self,values):
        self.matched+=1
        if self.matched>200000:raise StatisticsError('Statistics exceed 200,000 matching rows; choose an explicit filter or separately approved sample')
        group=tuple(values[c] for c in self.spec.by)
        if self.spec.by:
            code=self.group_ids.setdefault(group,len(self.group_ids));self.group_counts[group]+=1
            if len(self.group_ids)>64:raise StatisticsError('Grouped statistics exceed 64 groups; refine the declared grouping/filter')
        row=[];valid=True
        for c in self.columns:
            raw=values[c]
            if raw=='' or raw in self.missing_values.get(c,[]):
                self.missing[c]+=1;valid=False;row.append(0);continue
            try:v=float(raw)
            except ValueError:v=math.nan
            if not math.isfinite(v) or abs(v)>1e12:self.invalid[c]+=1;valid=False;row.append(0)
            else:row.append(v)
        if self.cluster and (values[self.cluster]=='' or values[self.cluster] in self.missing_values.get(self.cluster,[])):
            self.missing_clusters+=1;valid=False
        if not valid:self.excluded+=1;return
        self.values.extend(row)
        if self.spec.by:self.group_rows.append(self.group_ids[group])
        if self.cluster:
            code=self.cluster_ids.setdefault(values[self.cluster],len(self.cluster_ids));self.groups.append(code)
    def result(self):
        if self.excluded and self.spec.missing_policy=='error':raise StatisticsError('Selected statistical fields contain missing, invalid or non-finite values. Declare complete_cases or correct the variables/missing-token policy; no rows were silently removed.')
        try:
            import numpy as np
            from scipy import stats
        except ImportError:raise StatisticsError('Statistical runtime unavailable. Install the project statistics dependency profile in the launcher environment.') from None
        n=self.matched-self.excluded
        if not n:raise StatisticsError('No complete numeric rows remain for the selected statistical methods')
        data=np.asarray(self.values).reshape(n,len(self.columns));index={c:i for i,c in enumerate(self.columns)}
        result={'schema_version':'table-statistics-v1','methods':self.spec.methods,'specification':self.spec.model_dump(mode='json'),'matching_rows':self.matched,'analysis_rows':n,
                'excluded_rows':self.excluded,'missing_policy':self.spec.missing_policy,'missing_counts':self.missing,'invalid_counts':self.invalid,
                'missing_cluster_rows':self.missing_clusters,'ddof':self.spec.ddof,'quantile_method':'linear','descriptive':[],
                'grouped_descriptive':[],'correlations':[],'regression':None,'limitations':['Exploratory analysis, not causal identification or out-of-sample predictive validation.',
                'Selected numerical meaning and statistical assumptions require review; numeric syntax alone does not establish suitability.',
                'All methods use the same explicitly selected complete-case rows; correlation P-values are unadjusted and assume independent observations.']}
        def describe(frame):
            rows=[];count=len(frame)
            for c in self.spec.columns:
                v=frame[:,index[c]]
                rows.append({'column':c,'count':count,'mean':float(v.mean()) if count else None,'minimum':float(v.min()) if count else None,'maximum':float(v.max()) if count else None,
                    'variance':float(v.var(ddof=self.spec.ddof)) if count>self.spec.ddof else None,'standard_deviation':float(v.std(ddof=self.spec.ddof)) if count>self.spec.ddof else None,
                    'percentiles':{str(p):float(np.quantile(v,p/100,method='linear')) if count else None for p in self.spec.percentiles}})
            return rows
        if 'describe' in self.spec.methods:
            result['descriptive']=describe(data)
            for key,code in self.group_ids.items():
                frame=data[np.asarray(self.group_rows)==code]
                result['grouped_descriptive'].append({'group':dict(zip(self.spec.by,key)),'matching_rows':self.group_counts[key],'analysis_rows':len(frame),'descriptive':describe(frame)})
        if 'covariance' in self.spec.methods:
            if n<=self.spec.ddof:raise StatisticsError('Covariance needs more complete rows than ddof')
            frame=data[:,[index[c] for c in self.spec.columns]]
            centered=frame-frame.mean(axis=0)
            result['covariance_matrix']={'columns':self.spec.columns,'values':((centered.T@centered)/(n-self.spec.ddof)).tolist(),'rows':n,'ddof':self.spec.ddof}
        for method in ('pearson','spearman'):
            if method not in self.spec.methods:continue
            if n<3:raise StatisticsError('Correlation inference requires at least three complete rows')
            names=self.spec.columns;k=len(names);coefficients=[[None]*k for _ in names];pvalues=[[None]*k for _ in names]
            valid=[i for i,c in enumerate(names) if np.ptp(data[:,index[c]])>0]
            if method=='spearman' and len(valid)>=2:
                fit=stats.spearmanr(data[:,[index[names[i]] for i in valid]],axis=0)
                r=np.asarray(fit.statistic);p=np.asarray(fit.pvalue)
                if len(valid)==2:r=np.array([[1,float(r)],[float(r),1]]);p=np.array([[0,float(p)],[float(p),0]])
                for a,i in enumerate(valid):
                    for b,j in enumerate(valid):coefficients[i][j]=float(r[a,b]);pvalues[i][j]=float(p[a,b]) if i!=j else None
            else:
                for i in valid:
                    coefficients[i][i]=1.
                    for j in valid:
                        if j<=i:continue
                        fit=stats.pearsonr(data[:,index[names[i]]],data[:,index[names[j]]])
                        coefficients[i][j]=coefficients[j][i]=float(fit.statistic);pvalues[i][j]=pvalues[j][i]=float(fit.pvalue)
            result['correlations'].append({'method':method,'columns':names,'coefficients':coefficients,'p_values':pvalues,'rows':n,
                'constant_columns':[names[i] for i in range(k) if i not in valid],
                'inference':'Two-sided unadjusted; Spearman P-values use an asymptotic approximation, especially limited for small/tied samples.'})
        if self.spec.regression:
            try:from statsmodels.regression.linear_model import OLS
            except ImportError:raise StatisticsError('Linear regression requires the project statistics dependency profile (statsmodels).') from None
            s=self.spec.regression;y=data[:,index[s.outcome]];x=data[:,[index[c] for c in s.predictors]]
            if s.intercept:x=np.column_stack([np.ones(n),x])
            if n<=x.shape[1]:raise StatisticsError('Regression needs more complete observations than fitted parameters')
            if np.ptp(y)==0:raise StatisticsError('Regression outcome is constant; R-squared and inference would be unsuitable')
            if np.linalg.matrix_rank(x)<x.shape[1]:raise StatisticsError('Regression design is rank-deficient; remove redundant/constant predictors')
            if np.linalg.cond(x)>1e12:raise StatisticsError('Regression design is poorly conditioned; rescale or revise predictors')
            kw={}
            if s.covariance=='cluster':
                if len(self.cluster_ids)<2:raise StatisticsError('Cluster covariance needs at least two independent clusters')
                kw={'groups':np.asarray(self.groups),'use_correction':True}
            fit=OLS(y,x,missing='raise',hasconst=s.intercept).fit(cov_type=s.covariance,cov_kwds=kw,use_t=True)
            perfect=bool(np.max(np.abs(fit.resid))<=np.finfo(float).eps*64*max(1,float(np.linalg.norm(y)/math.sqrt(n))))
            ci=fit.conf_int(alpha=1-s.confidence_level)
            finite_inference=bool(np.isfinite(fit.bse).all() and np.isfinite(fit.pvalues).all() and np.isfinite(ci).all())
            unavailable=perfect or not finite_inference
            def number(v):return float(v) if np.isfinite(v) else None
            terms=(['Intercept'] if s.intercept else [])+s.predictors
            result['regression']={'method':'OLS','outcome':s.outcome,'predictors':s.predictors,'intercept':s.intercept,'covariance':s.covariance,
                'rows':n,'clusters':len(self.cluster_ids) if self.cluster else None,'confidence_level':s.confidence_level,
                'degrees_of_freedom_residual':float(fit.df_resid),'degrees_of_freedom_inference':float(getattr(fit,'df_resid_inference',fit.df_resid)),
                'r_squared':number(fit.rsquared),'adjusted_r_squared':number(fit.rsquared_adj),'r_squared_kind':'centered' if s.intercept else 'uncentered',
                'residual_standard_error':number(math.sqrt(float(fit.ssr/fit.df_resid))),'condition_number':number(fit.condition_number),
                'inference_status':'unavailable_perfect_fit' if perfect else 'unavailable_non_finite_covariance' if not finite_inference else 'conditional_on_declared_assumptions',
                'coefficients':[{'term':term,'coefficient':number(fit.params[i]),'standard_error':None if unavailable else number(fit.bse[i]),
                    't_statistic':None if unavailable else number(fit.tvalues[i]),'p_value':None if unavailable else number(fit.pvalues[i]),
                    'confidence_lower':None if unavailable else number(ci[i,0]),'confidence_upper':None if unavailable else number(ci[i,1])} for i,term in enumerate(terms)],
                'diagnostics':{'durbin_watson':number(np.sum(np.diff(fit.resid)**2)/fit.ssr) if fit.ssr>0 else None,'leverage_max':number(fit.get_influence().hat_matrix_diag.max())}}
            result['limitations'].append('OLS coefficients/P-values are conditional on specification, sampling and covariance assumptions; they do not establish causality.')
            if perfect:result['limitations'].append('Perfect/nearly perfect fit: coefficient inference is deliberately unavailable.')
            if not finite_inference:result['limitations'].append('Non-finite covariance/inference: coefficient standard errors, tests and intervals are unavailable; revise the design/covariance assumptions.')
            if self.cluster and len(self.cluster_ids)<30:result['limitations'].append('Fewer than 30 clusters: cluster-robust inference may be unreliable.')
        from importlib.metadata import version
        result['runtime_versions']={p:version(p) for p in ('numpy','scipy')}
        if self.spec.regression:result['runtime_versions']['statsmodels']=version('statsmodels')
        result['report_markdown']=render_report(result)
        return result

def render_report(result):
    def cell(value):
        if value is None:return 'Unavailable'
        if isinstance(value,float):value=format(value,'.12g')
        return str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>').replace('\r','')
    def table(headers,rows):
        return ['| '+' | '.join(cell(v) for v in headers)+' |','| '+' | '.join('---' for _ in headers)+' |',*('| '+' | '.join(cell(v) for v in row)+' |' for row in rows),'']
    spec=result.get('specification') or {}
    lines=['# Statistical analysis report','',f"Methods: {', '.join(result['methods'])}.",'','## Analysis definition','',*table(['Definition','Value'],[
        ('Question supplied by user/planner',spec.get('question') or 'Not supplied; this report describes the declared methods and fields.'),
        ('Selected numerical fields',', '.join(spec.get('columns',[])) or 'See explicit regression outcome and predictors.'),
        ('Grouping fields',', '.join(spec.get('by',[])) or 'No grouping'),
        ('Observation unit','Parsed rows; domain unit and independence are not established by this report.'),
        ('Interpretation','Computed facts below are separate from any advisory agent interpretation.')]),
        '## Scope and source','',*table(['Scope','Value'],[
        ('Matching rows',result['matching_rows']),('Analyzed complete rows',result['analysis_rows']),('Excluded rows',result['excluded_rows']),('Missing policy',result['missing_policy']),
        ('Variance / SD / covariance denominator',f"n - {result['ddof']}"),('Percentile method',result['quantile_method'])])]
    if result.get('source'):lines+=table(['Source evidence','Value'],[('Source',result['source']['path']),('SHA-256',result['source']['sha256']),('Source rows',result['source_rows'])])
    if result.get('source_selection'):lines+=['### Selected source table','',*table(['Selection','Value'],result['source_selection'].items())]
    if result.get('filters'):lines+=['### Applied exact-text filters','',*table(['Field','Required value'],[(f['column'],f['value']) for f in result['filters']])]
    lines+=['## Computed findings','',*table(['Evidence','Observed result'],[
        ('Analysis population',f"{result['analysis_rows']} of {result['matching_rows']} matching rows; {result['excluded_rows']} excluded"),
        *[(d['column'],f"n={d['count']}; mean={d['mean']}; minimum={d['minimum']}; maximum={d['maximum']}") for d in result['descriptive']],
        ('Recorded groups',len(result['grouped_descriptive']))]),
        'These are descriptive/computational facts. Units, representativeness, clinical meaning and causality are not established.','']
    def descriptive(rows):
        return table(['Field','Count','Mean','Minimum','Maximum','Variance','Standard deviation'],[(d['column'],d['count'],d['mean'],d['minimum'],d['maximum'],d['variance'],d['standard_deviation']) for d in rows])+table(['Field','Percentile','Value'],[(d['column'],p,v) for d in rows for p,v in d['percentiles'].items()])
    if result['descriptive']:lines+=['## Descriptive statistics','',*descriptive(result['descriptive'])]
    for i,g in enumerate(result['grouped_descriptive']):
        lines += [f"### Group {i+1}",'',*table(['Grouping field','Value'],g['group'].items()),f"Analyzed rows: {g['analysis_rows']}; matching rows: {g['matching_rows']}.",'',*descriptive(g['descriptive'])]
    lines += ['## Missing and invalid values','',*table(['Field','Missing','Invalid'],[(c,result['missing_counts'][c],result['invalid_counts'][c]) for c in result['missing_counts']])]
    if result.get('missing_cluster_rows'):lines += [f"Missing cluster rows: {result['missing_cluster_rows']}.",'']
    for c in result['correlations']:
        lines += [f"## {c['method'].title()} correlation",'',f"Complete rows: {c['rows']}. {c['inference']}",'']
        for title,key in [('Coefficients','coefficients'),('Unadjusted P-values','p_values')]:
            lines += [f'### {title}','',*table(['Field',*c['columns']],[(name,*row) for name,row in zip(c['columns'],c[key])])]
    covariance=result.get('covariance_matrix')
    if covariance:lines += ['## Covariance matrix','',f"Complete rows: {covariance['rows']}; denominator: n - {covariance['ddof']}.",'',*table(['Field',*covariance['columns']],[(name,*row) for name,row in zip(covariance['columns'],covariance['values'])])]
    r=result['regression']
    if r:
        lines += ['## Linear regression','',*table(['Model fact','Value'],[(k.replace('_',' ').capitalize(),v) for k,v in r.items() if k not in {'coefficients','diagnostics','predictors'}]),*table(['Predictor'],[(p,) for p in r['predictors']]),
            '### Coefficients and conditional inference','',*table(['Term','Coefficient','Standard error','t statistic','P-value','Confidence lower','Confidence upper'],[[c[k] for k in ('term','coefficient','standard_error','t_statistic','p_value','confidence_lower','confidence_upper')] for c in r['coefficients']]),
            '### Diagnostics','',*table(['Diagnostic','Value'],[(k.replace('_',' ').capitalize(),v) for k,v in r['diagnostics'].items()])]
    if result.get('runtime_versions'):lines += ['## Runtime versions','',*table(['Package','Version'],result['runtime_versions'].items())]
    return '\n'.join([*lines,'## Limitations','',*('- '+v for v in result['limitations'])])+'\n'


def statistical_evidence(outcome):
    """Compact aggregate handoff to model review; never includes raw input rows."""
    value=(outcome.get('table_analysis') or {}).get('statistics')
    if not value:return None
    r=value.get('regression')
    correlations=[]
    for c in value['correlations']:
        pairs=[{'fields':[a,b],'coefficient':c['coefficients'][i][j],'p_value':c['p_values'][i][j]}
            for i,a in enumerate(c['columns']) for j,b in enumerate(c['columns']) if j>i]
        correlations.append({**{k:c[k] for k in ('method','rows','columns','constant_columns','inference')},'pairs':pairs[:6],'pairs_omitted':max(0,len(pairs)-6)})
    covariance=value.get('covariance_matrix')
    from copy import deepcopy
    result=deepcopy({'methods':value['methods'],'source':value.get('source'),'source_rows':value.get('source_rows'),'source_selection':value.get('source_selection'),
            'question':(value.get('specification') or {}).get('question'),'specification':value.get('specification'),
            'matching_rows':value['matching_rows'],'analysis_rows':value['analysis_rows'],'excluded_rows':value['excluded_rows'],
            'missing_counts':value['missing_counts'],'invalid_counts':value['invalid_counts'],
            'group_count':len(value['grouped_descriptive']),'grouped_descriptive':value['grouped_descriptive'][:3],
            'group_summaries_omitted':max(0,len(value['grouped_descriptive'])-3),
            'correlations':correlations,
            'covariance':{k:covariance[k] for k in ('columns','rows','ddof')} if covariance else None,
            'descriptive':value['descriptive'][:8],
            'regression':{k:r[k] for k in ('outcome','covariance','rows','clusters','r_squared','adjusted_r_squared','inference_status','coefficients','condition_number','diagnostics','degrees_of_freedom_residual')} if r else None,
            'limitations':value['limitations']})
    result['descriptive_fields_omitted']=max(0,len(value['descriptive'])-len(result['descriptive']))
    import json
    if len(json.dumps(result).encode())>6000:
        result['grouped_descriptive']=[]
        result['group_summaries_omitted']=result['group_count']
    while len(json.dumps(result).encode())>6000 and result['descriptive']:
        result['descriptive'].pop();result['descriptive_fields_omitted']+=1
    if len(json.dumps(result).encode())>6000:
        # A bounded review must retain scope/diagnostic gaps rather than silently
        # substitute an empty pack. The complete recorded report is untouched.
        for name in ('specification','missing_counts','invalid_counts','correlations','covariance','regression'):
            result.pop(name,None)
        result['evidence_omissions']='Detailed specification, missing/invalid counts, matrices and model evidence exceeded review budget; inspect the complete recorded report before conclusions.'
    return result
