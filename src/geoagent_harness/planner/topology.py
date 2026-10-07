"""Deterministic operation dependencies; absent fields retain legacy ordering."""
from geoagent_harness.planner.schemas import WorkflowPlan


def plan_dependencies(plan: WorkflowPlan) -> dict[str, list[str]]:
    dependencies = {
        step.step_id: (list(step.depends_on) if step.depends_on is not None else
                       ([] if index == 0 else [plan.steps[index - 1].step_id]))
        for index, step in enumerate(plan.steps)
    }
    known = set(dependencies)
    for step_id, parents in dependencies.items():
        if len(parents) != len(set(parents)):
            raise ValueError('operation dependencies must be unique')
        if step_id in parents:
            raise ValueError('an operation cannot depend on itself')
        if not set(parents).issubset(known):
            raise ValueError('operation dependency references an unknown step')
    return dependencies


def plan_topological_order(plan: WorkflowPlan) -> list[str]:
    remaining = {key: set(value) for key, value in plan_dependencies(plan).items()}
    order = []
    while remaining:
        ready = [key for key, parents in remaining.items() if not parents]
        if not ready:
            raise ValueError('operation dependencies contain a cycle')
        for key in ready:
            order.append(key)
            remaining.pop(key)
        for parents in remaining.values():
            parents.difference_update(ready)
    return order


def ancestors(step_id: str, dependencies: dict[str, list[str]]) -> set[str]:
    found = set()
    pending = list(dependencies[step_id])
    while pending:
        current = pending.pop()
        if current not in found:
            found.add(current)
            pending.extend(dependencies[current])
    return found
