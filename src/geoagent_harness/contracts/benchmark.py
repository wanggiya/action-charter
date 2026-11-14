"""Benchmark definitions and observations; none of these records grants authority."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r'^[a-z0-9][a-z0-9_-]{0,79}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Count = Annotated[StrictInt, Field(ge=0)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
NonnegativeNumber = Annotated[Number, Field(ge=0)]
DataClass = Literal['none', 'metadata', 'data_card', 'aggregates', 'raw']
ExpectedKind = Literal['deterministic', 'gold_set', 'refusal', 'unsupported']


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, str_strip_whitespace=False)


def relative_path(value: str) -> str:
    """Portable normalized locator, not an authorization or a path resolver."""
    if (not value or len(value) > 500 or '\\' in value or ':' in value
            or any(not c.isprintable() for c in value)
            or any(part in {'', '.', '..'} for part in value.split('/'))
            or any(part != part.strip() for part in value.split('/'))):
        raise ValueError('Choose a normalized relative path')
    return value


class ColumnsCheck(BenchmarkModel):
    type: Literal['report_contains_columns']
    step_id: Annotated[str, Field(pattern=r'^step_[1-9][0-9]*$')] | None = None
    skill_id: Identifier | None = None
    columns: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=160)], ...], Field(min_length=1, max_length=256)]

    @model_validator(mode='after')
    def one_selector(self):
        if self.step_id and self.skill_id:raise ValueError('Choose step_id or skill_id, not both')
        return self


class ValueCheck(BenchmarkModel):
    type: Literal['value_close']
    field: Annotated[str, Field(min_length=1, max_length=300)]
    expected: Number
    tolerance: NonnegativeNumber


class RowCountCheck(BenchmarkModel):
    type: Literal['row_count']
    field: Annotated[str, Field(min_length=1, max_length=300)]
    expected: Count


class FileCheck(BenchmarkModel):
    type: Literal['file_exists']
    path: Annotated[str, Field(min_length=1, max_length=500)]
    expected_sha256: Digest | None = None

    @field_validator('path')
    @classmethod
    def safe_output(cls, value):
        value = relative_path(value)
        if not value.startswith('data/output/'):
            raise ValueError('Expected outputs must be under data/output')
        return value


class TableCheck(BenchmarkModel):
    type: Literal['table_exists']
    schema_name: Annotated[str, Field(pattern=r'^[a-z_][a-z0-9_]{0,62}$')]
    table: Annotated[str, Field(pattern=r'^[a-z_][a-z0-9_]{0,62}$')]


class NoFileOutputsCheck(BenchmarkModel):
    type: Literal['no_file_outputs']


Check = Annotated[ColumnsCheck | ValueCheck | RowCountCheck | FileCheck | TableCheck | NoFileOutputsCheck, Field(discriminator='type')]


class DeterministicExpected(BenchmarkModel):
    kind: Literal['deterministic']
    checks: Annotated[tuple[Check, ...], Field(min_length=1, max_length=64)]


class GoldExpected(BenchmarkModel):
    kind: Literal['gold_set']
    path: str

    @field_validator('path')
    @classmethod
    def safe_gold_path(cls, value):
        value = relative_path(value)
        if not value.startswith('expected/'):
            raise ValueError('Gold labels must be under expected')
        return value


class RefusalExpected(BenchmarkModel):
    kind: Literal['refusal']
    nothing_executed: Literal[True] = True


class UnsupportedExpected(BenchmarkModel):
    kind: Literal['unsupported']
    reason_code: Identifier


Expected = Annotated[DeterministicExpected | GoldExpected | RefusalExpected | UnsupportedExpected, Field(discriminator='kind')]


class BenchmarkLimits(BenchmarkModel):
    wall_clock_s: Annotated[Number, Field(gt=0, le=86400)] = 600
    model_calls: Annotated[StrictInt, Field(ge=0, le=1000)] = 20


class BenchmarkTask(BenchmarkModel):
    schema_version: Literal['1.0'] = '1.0'
    id: Identifier
    workload: Literal['H', 'E', 'PA', 'G', 'S']
    title: Annotated[str, Field(min_length=1, max_length=160)]
    request: Annotated[str, Field(min_length=1, max_length=8000)]
    inputs: Annotated[tuple[str, ...], Field(max_length=32)]
    requires_local_data: StrictBool = False
    write_mode: Literal['read_only', 'fixture'] = 'read_only'
    runtime: Literal['local', 'postgis'] = 'local'
    requires_gis: StrictBool = False
    data_class: DataClass
    expected: Expected
    limits: BenchmarkLimits = Field(default_factory=BenchmarkLimits)

    @field_validator('title', 'request')
    @classmethod
    def meaningful_text(cls, value):
        if not value.strip() or '\x00' in value:
            raise ValueError('Text must be nonempty and contain no NUL')
        return value

    @model_validator(mode='after')
    def input_contract(self):
        if self.requires_local_data and (self.runtime!='local' or self.write_mode!='read_only'):
            raise ValueError('Local-data benchmarks are read-only and cannot use disposable database fixtures')
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError('Duplicate input locators')
        for value in self.inputs:
            relative_path(value)
            if not value.startswith('input/') and not (self.requires_local_data and value.startswith('data/input/')):
                raise ValueError('Use input/ fixtures, or explicit requires_local_data with data/input/')
        return self


class RoleMetrics(BenchmarkModel):
    role: Identifier
    model_calls: Count
    prompt_tokens: Count | None = None
    completion_tokens: Count | None = None
    elapsed_seconds: NonnegativeNumber | None = None


class BenchmarkMetrics(BenchmarkModel):
    model_calls: Count
    wall_seconds: NonnegativeNumber
    prompt_tokens: Count | None = None
    completion_tokens: Count | None = None
    process_cpu_seconds: NonnegativeNumber | None = None
    process_sampled_peak_rss_bytes: Count | None = None
    retries: Count = 0
    timeouts: Count = 0
    approvals_required: Count = 0
    roles: Annotated[tuple[RoleMetrics, ...], Field(max_length=32)] = Field(default_factory=tuple)

    @model_validator(mode='after')
    def role_totals(self):
        if len({r.role for r in self.roles}) != len(self.roles):
            raise ValueError('Duplicate role metrics')
        if self.roles and sum(r.model_calls for r in self.roles) != self.model_calls:
            raise ValueError('Role calls must sum to observed model calls')
        return self


class BenchmarkModelConfiguration(BenchmarkModel):
    timeout_seconds: Annotated[Number, Field(gt=0, le=600)]
    max_tokens: Annotated[StrictInt, Field(ge=1, le=32768)]
    reasoning_effort: Literal['none', 'low', 'medium', 'high'] | None
    response_format: Literal['json_schema', 'json_object']


class BenchmarkRunContext(BenchmarkModel):
    started_at: Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')]
    task_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=256)]
    source_sha256: Digest
    python_version: Annotated[str, Field(pattern=r'^\d+\.\d+\.\d+$')]
    package_versions: dict[Identifier, Annotated[str, Field(pattern=r'^[A-Za-z0-9.+_-]{1,100}$')]]
    model_configuration: BenchmarkModelConfiguration | None
    allow_fixture_writes: StrictBool
    disposable_database: StrictBool
    include_local_data: StrictBool


class CheckResult(BenchmarkModel):
    check_index: Annotated[StrictInt, Field(ge=0, le=63)]
    status: Literal['passed', 'failed', 'error']
    reason_code: Identifier


class BenchmarkResult(BenchmarkModel):
    schema_version: Literal['1.0'] = '1.0'
    run_id: Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
    task_id: Identifier
    task_sha256: Digest
    evidence_kind: Literal['fixture', 'real_model']
    provider_profile_id: Identifier
    model: Annotated[str, Field(min_length=1, max_length=160)] | None = None
    code_version: Annotated[str, Field(pattern=r'^[a-f0-9]{40}(?:[a-f0-9]{24})?$')] | None
    source_dirty: StrictBool | None
    egress_class: DataClass
    expected_kind: ExpectedKind
    status: Literal['passed', 'failed', 'timeout', 'error', 'skipped', 'unsupported']
    observed_outcome: Literal['completed', 'refused', 'unsupported', 'not_dispatched', 'error', 'unknown']
    executed_operations: Count | None = None
    reason_code: Identifier
    checks: Annotated[tuple[CheckResult, ...], Field(max_length=64)] = Field(default_factory=tuple)
    advisory_status: Literal['complete', 'unavailable', 'not_requested', 'deferred', 'unknown'] = 'not_requested'
    metrics: BenchmarkMetrics

    @model_validator(mode='after')
    def consistent_evidence(self):
        if self.evidence_kind == 'real_model' and not self.model:
            raise ValueError('Real-model evidence requires a model identity')
        if len({c.check_index for c in self.checks}) != len(self.checks):
            raise ValueError('Duplicate check results')
        if self.status == 'passed':
            if any(c.status != 'passed' for c in self.checks):
                raise ValueError('Passing tasks cannot contain failed or errored checks')
            if self.expected_kind == 'unsupported':
                raise ValueError('Unsupported capability is a gap, not a passing task')
            if self.expected_kind == 'refusal':
                if self.observed_outcome != 'refused' or self.executed_operations != 0:
                    raise ValueError('Passing refusal requires observed refusal and zero executed operations')
            elif self.observed_outcome != 'completed' or not self.checks or any(c.status != 'passed' for c in self.checks):
                raise ValueError('Passing analysis requires completed work and passing checks')
        if self.status == 'unsupported' and (self.expected_kind != 'unsupported'
                or self.observed_outcome != 'unsupported' or self.executed_operations != 0):
            raise ValueError('Unsupported gaps must be explicit with no executed operations')
        if self.status == 'skipped' and (self.observed_outcome != 'not_dispatched'
                or self.executed_operations != 0 or self.metrics.model_calls != 0):
            raise ValueError('Skipped tasks must not dispatch work')
        return self
