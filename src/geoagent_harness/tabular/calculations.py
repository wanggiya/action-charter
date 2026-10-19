"""Versioned, bounded expression data. No Python evaluation or dynamic dispatch."""
from __future__ import annotations

import json
import math
from typing import Annotated, Literal, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Column(Closed):
    kind: Literal['column']
    name: str = Field(min_length=1, max_length=200)


class Number(Closed):
    kind: Literal['number']
    value: StrictInt | StrictFloat


class Binary(Closed):
    kind: Literal['binary']
    operator: Literal['add', 'subtract', 'multiply', 'divide']
    left: 'Expression'
    right: 'Expression'


class Compare(Closed):
    kind: Literal['compare']
    operator: Literal['eq', 'ne', 'gt', 'ge', 'lt', 'le']
    left: 'Expression'
    right: 'Expression'


class Conditional(Closed):
    kind: Literal['if']
    condition: 'Expression'
    then: 'Expression'
    otherwise: 'Expression'


Expression = Annotated[Union[Column, Number, Binary, Compare, Conditional], Field(discriminator='kind')]
for model in (Binary, Compare, Conditional):
    model.model_rebuild()


class DerivedColumn(Closed):
    output_column: str = Field(min_length=1, max_length=200)
    expression: Expression


def bounded_definition(value):
    """Run before recursive Pydantic parsing, including on untrusted API inputs."""
    if not isinstance(value, dict):
        return value
    definitions = value.get('calculations', [])
    try:
        encoded = json.dumps(definitions, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError('Calculation definition must be finite JSON') from error
    if len(encoded) > 8192:
        raise ValueError('Calculation definition exceeds 8 KiB')
    pending = [(item.get('expression'), 1) for item in definitions if isinstance(item, dict)] if isinstance(definitions, list) else []
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > 100 or depth > 8:
            raise ValueError('Calculations exceed 100 expression nodes or depth eight')
        if isinstance(node, dict):
            pending.extend((node[key], depth + 1) for key in ('left', 'right', 'condition', 'then', 'otherwise') if key in node)
    return value


def expression_type(node):
    if isinstance(node, Column):
        return 'number'
    if isinstance(node, Number):
        try:
            finite = math.isfinite(float(node.value))
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError('Calculation numbers must be finite float64 values')
        return 'number'
    if isinstance(node, (Binary, Compare)):
        if expression_type(node.left) != 'number' or expression_type(node.right) != 'number':
            raise ValueError('Arithmetic and comparisons require numeric operands')
        return 'boolean' if isinstance(node, Compare) else 'number'
    if expression_type(node.condition) != 'boolean' or expression_type(node.then) != 'number' or expression_type(node.otherwise) != 'number':
        raise ValueError('Conditional requires a comparison and two numeric branches')
    return 'number'


def column_names(node):
    if isinstance(node, Column):
        return {node.name}
    if isinstance(node, Number):
        return set()
    children = (node.left, node.right) if isinstance(node, (Binary, Compare)) else (node.condition, node.then, node.otherwise)
    return set().union(*(column_names(child) for child in children))


def numeric_inputs(frame, args):
    from .service import TabularError, _numeric
    outputs = [item.output_column for item in args.calculations]
    if len(set(outputs)) != len(outputs) or set(outputs) & set(frame.columns):
        raise TabularError('Calculation output columns must be unique and must not replace source columns')
    if len(frame.columns) + len(outputs) > 100:
        raise TabularError('Calculation would exceed 100 columns')
    names = set().union(*(column_names(item.expression) for item in args.calculations))
    if names - set(frame.columns):
        raise TabularError('Calculation references unknown original source columns')
    columns = {}
    for name in names:
        series = _numeric(frame[name]).astype('Float64')
        if args.missing_policy == 'error' and series.isna().any():
            raise TabularError('Calculation has missing inputs; handle missing values or explicitly choose propagate')
        columns[name] = series
    return columns


def calculate(frame, args):
    from .service import TabularError
    columns = numeric_inputs(frame, args)

    def evaluate(node, index):
        if isinstance(node, Column):
            return columns[node.name].loc[index]
        if isinstance(node, Number):
            return pd.Series(float(node.value), index=index, dtype='Float64')
        if isinstance(node, Conditional):
            condition = evaluate(node.condition, index)
            result = pd.Series(pd.NA, index=index, dtype='Float64')
            # Only evaluate selected branches: an inactive divide-by-zero is harmless.
            for flag, branch in ((True, node.then), (False, node.otherwise)):
                selected = index[condition.eq(flag).fillna(False)]
                if len(selected):
                    result.loc[selected] = evaluate(branch, selected)
            return result
        left, right = evaluate(node.left, index), evaluate(node.right, index)
        if isinstance(node, Compare):
            return {'eq': left.eq, 'ne': left.ne, 'gt': left.gt, 'ge': left.ge, 'lt': left.lt, 'le': left.le}[node.operator](right)
        if node.operator == 'divide' and (right.eq(0) & left.notna()).fillna(False).any():
            raise TabularError('Calculation division by zero')
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            result = {'add': left.add, 'subtract': left.sub, 'multiply': left.mul, 'divide': left.div}[node.operator](right)
        if any(not math.isfinite(float(value)) for value in result.dropna()):
            raise TabularError('Calculation overflow or non-finite result')
        # A missing result from two present inputs is an invalid numeric operation.
        if (result.isna() & left.notna() & right.notna()).any():
            raise TabularError('Calculation produced an invalid numeric result')
        return result

    result = frame.copy()
    for item in args.calculations:
        result[item.output_column] = evaluate(item.expression, frame.index)
    return result


def verify_calculation(source, output, args):
    """Independent scalar interpreter checks all serialized rows, not model claims."""
    from .service import TabularError
    numeric_inputs(source, args)

    def scalar(node, row):
        if isinstance(node, Column):
            return None if pd.isna(row[node.name]) else float(row[node.name])
        if isinstance(node, Number):
            return float(node.value)
        if isinstance(node, Conditional):
            condition = scalar(node.condition, row)
            return None if condition is None else scalar(node.then if condition else node.otherwise, row)
        left, right = scalar(node.left, row), scalar(node.right, row)
        if left is None or right is None:
            return None
        if isinstance(node, Compare):
            if node.operator == 'eq': return left == right
            if node.operator == 'ne': return left != right
            if node.operator == 'gt': return left > right
            if node.operator == 'ge': return left >= right
            if node.operator == 'lt': return left < right
            return left <= right
        if node.operator == 'add': value = left + right
        elif node.operator == 'subtract': value = left - right
        elif node.operator == 'multiply': value = left * right
        else: value = left / right
        if not math.isfinite(value):
            raise TabularError('Calculation verification found a non-finite result')
        return value

    expected_columns = [*source.columns, *(item.output_column for item in args.calculations)]
    if list(output.columns) != expected_columns or len(source) != len(output):
        return False
    if not source.reset_index(drop=True).equals(output.loc[:, source.columns].reset_index(drop=True)):
        return False
    for index, row in enumerate(source.to_dict(orient='records')):
        for item in args.calculations:
            expected, actual = scalar(item.expression, row), output.iloc[index][item.output_column]
            if expected is None:
                if not pd.isna(actual): return False
            elif pd.isna(actual) or not math.isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-12):
                return False
    return True
