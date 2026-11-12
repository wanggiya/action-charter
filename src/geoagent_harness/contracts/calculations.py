"""Versioned, bounded expression data. No Python evaluation or dynamic dispatch."""
from __future__ import annotations

import json
import math
from typing import Annotated, Literal, Union

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


