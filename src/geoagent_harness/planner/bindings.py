"""Mechanical proposal bindings; never authority or filesystem output creation."""
from uuid import uuid4
import re

from geoagent_harness.tabular.schemas import is_table_write


def fresh_csv_path():
    return 'data/output/result_' + uuid4().hex + '.csv'


def allocate_csv_outputs(plan):
    """Only infer the format already fixed by the registered CSV contract."""
    assigned=[]
    for step in plan.steps:
        if is_table_write(step.skill) and 'target_path' not in step.arguments:
            step.arguments['target_path']=fresh_csv_path()
            assigned.append(step.step_id)
    return assigned


def refresh_automatic_targets(plan,base,root):
    """A revised workflow must not rerun writes into occupied auto-owned paths."""
    from geoagent_harness.approvals import plan_sha256
    if base is None or plan_sha256(plan)==plan_sha256(base.plan):
        return []
    old={s.arguments.get('target_path') for s in base.plan.steps if is_table_write(s.skill)}
    refreshed=[]
    for step in plan.steps:
        target=step.arguments.get('target_path')
        if is_table_write(step.skill) and isinstance(target,str) and target in old and re.fullmatch(r'data/output/result_[a-f0-9]{32}\.csv',target) and (root/target).exists():
            step.arguments['target_path']=fresh_csv_path()
            refreshed.append(step.step_id)
    return refreshed


def automatic_recipe_parameters(recipe):
    def references(value):
        if isinstance(value,dict):
            if set(value)=={'$parameter'}:
                return {value['$parameter']}
            return set().union(*(references(v) for v in value.values()))
        if isinstance(value,list):
            return set().union(*(references(v) for v in value))
        return set()
    outputs=set()
    other=set()
    for step in recipe.steps:
        for name,value in step.arguments.items():
            if name=='target_path' and is_table_write(step.skill):
                outputs.update(references(value))
            else:
                other.update(references(value))
        if step.csv_source_parameter:
            other.add(step.csv_source_parameter)
    return sorted(name for name in outputs-other if name in recipe.parameters and recipe.parameters[name].type=='string')


def bind_recipe_parameters(recipe,supplied):
    values=dict(supplied)
    for name in automatic_recipe_parameters(recipe):
        if name not in values:
            values[name]=fresh_csv_path()
    return values


def bind_required_gates(plan, registry):
    """Raise required proposal gates from trusted contracts; never authorize work."""
    from geoagent_harness.planner.policy import WRITE_SKILLS
    known = {skill.id: skill for skill in registry.implemented_skills()}
    changed = []
    for step in plan.steps:
        skill = known.get(step.skill)
        if skill is None:
            continue  # The normal allowlist check rejects unknown operations.
        approval = skill.approval_required or skill.access.value != 'read_only' or step.skill in WRITE_SKILLS
        validation = skill.validation_required or is_table_write(step.skill) or step.skill in {'verify_snakemake_export', 'validate_postgis_layer'}
        if (approval and not step.requires_approval) or (validation and not step.validation_required):
            changed.append(step.step_id)
        step.requires_approval = bool(step.requires_approval or approval)
        step.validation_required = bool(step.validation_required or validation)
    return changed
