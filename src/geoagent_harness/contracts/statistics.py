from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator

class StatisticsError(ValueError):pass


class RegressionSpec(BaseModel):
    model_config=ConfigDict(extra='forbid')
    outcome:str=Field(min_length=1,max_length=200)
    predictors:list[str]=Field(min_length=1,max_length=12)
    intercept:bool=True
    covariance:Literal['nonrobust','HC3','cluster']='nonrobust'
    cluster_column:str|None=Field(default=None,min_length=1,max_length=200)
    confidence_level:float=Field(default=.95,ge=.8,le=.999)
    @model_validator(mode='after')
    def valid(self):
        if len(set(self.predictors))!=len(self.predictors) or self.outcome in self.predictors:
            raise ValueError('Outcome and unique predictors must be different fields')
        if (self.covariance=='cluster')!=(self.cluster_column is not None):
            raise ValueError('Cluster covariance requires cluster_column; other covariance methods do not accept it')
        if any(not c or len(c)>200 for c in self.predictors):raise ValueError('Predictor names exceed field limits')
        return self


class StatisticsSpec(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question:str|None=Field(default=None,min_length=1,max_length=400,description='User analysis question; untrusted context, not evidence or authority')
    methods:list[Literal['describe','pearson','spearman','covariance','linear_regression']]=Field(default_factory=lambda:['describe'],min_length=1,max_length=5)
    columns:list[str]=Field(default_factory=list,max_length=24)
    by:list[str]=Field(default_factory=list,max_length=2)
    percentiles:list[float]=Field(default_factory=lambda:[0.0,25.0,50.0,75.0,100.0],min_length=1,max_length=11)
    ddof:Literal[0,1]=1
    missing_policy:Literal['error','complete_cases']='error'
    regression:RegressionSpec|None=None
    @model_validator(mode='after')
    def valid(self):
        if len(set(self.methods))!=len(self.methods) or len(set(self.columns))!=len(self.columns):raise ValueError('Methods and column names must be unique')
        if any(not c or len(c)>200 for c in self.columns):raise ValueError('Column names exceed field limits')
        if any(not math.isfinite(p) or not 0<=p<=100 for p in self.percentiles) or len(set(self.percentiles))!=len(self.percentiles):raise ValueError('Percentiles must be unique numbers from 0 to 100')
        if any(m!='linear_regression' for m in self.methods) and not self.columns:raise ValueError('Choose numeric columns for descriptive/correlation methods')
        if any(m in self.methods for m in ('pearson','spearman','covariance')) and len(self.columns)<2:raise ValueError('Matrix analysis requires at least two numeric fields')
        if ('linear_regression' in self.methods)!=(self.regression is not None):raise ValueError('Linear regression requires its explicit outcome/predictor specification')
        if len(self.numeric_columns())>24:raise ValueError('Statistics support at most 24 selected numeric fields')
        if len(set(self.by))!=len(self.by) or any(not c or len(c)>200 for c in self.by):raise ValueError('Grouping fields must be unique bounded names')
        if self.by and 'describe' not in self.methods:raise ValueError('Statistical grouping currently requires describe; regression/correlation remain whole-matching-population methods')
        return self
    def numeric_columns(self):
        return list(dict.fromkeys(self.columns+([self.regression.outcome,*self.regression.predictors] if self.regression else [])))

