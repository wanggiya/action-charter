import type { InterfacePlannerResult } from "./interface-api";
type Step = InterfacePlannerResult["plan"]["steps"][number];

export function operationDependencies(steps: Step[]): Record<string, string[]> {
  return Object.fromEntries(steps.map((step, index) => [step.step_id,
    step.depends_on == null ? (index === 0 ? [] : [steps[index - 1].step_id]) : [...step.depends_on]]));
}
export function materializeDependencies(result: InterfacePlannerResult): InterfacePlannerResult {
  const next = structuredClone(result);
  const dependencies = operationDependencies(next.plan.steps);
  next.plan.steps = next.plan.steps.map((step) => ({ ...step, depends_on: dependencies[step.step_id] }));
  return next;
}
export function canConnectOperations(steps: Step[], from: string, to: string): boolean {
  const dependencies = operationDependencies(steps);
  if (from === to || !dependencies[from] || !dependencies[to] || dependencies[to].includes(from)) return false;
  const pending = [from];
  const seen = new Set<string>();
  while (pending.length) {
    const current = pending.pop()!;
    if (current === to) return false;
    if (!seen.has(current)) { seen.add(current); pending.push(...(dependencies[current] ?? [])); }
  }
  return true;
}
export function connectOperations(result: InterfacePlannerResult, from: string, to: string): InterfacePlannerResult {
  if (!canConnectOperations(result.plan.steps, from, to)) throw new Error("Connection is duplicated, invalid or would create a cycle.");
  const next = materializeDependencies(result);
  next.plan.steps.find((step) => step.step_id === to)!.depends_on!.push(from);
  return next;
}
export function disconnectOperations(result: InterfacePlannerResult, from: string, to: string): InterfacePlannerResult {
  const next = materializeDependencies(result);
  const target = next.plan.steps.find((step) => step.step_id === to);
  if (!target || !target.depends_on!.includes(from)) throw new Error("Select an existing connection.");
  target.depends_on = target.depends_on!.filter((id) => id !== from);
  return next;
}
export function deleteOperation(result: InterfacePlannerResult, id: string): InterfacePlannerResult {
  if (result.plan.steps.length <= 1) throw new Error("Keep at least one operation.");
  const next = materializeDependencies(result);
  const remaining = next.plan.steps.filter((step) => step.step_id !== id);
  const renamed = Object.fromEntries(remaining.map((step, index) => [step.step_id, `step_${index + 1}`]));
  next.plan.steps = remaining.map((step) => ({ ...step, step_id: renamed[step.step_id], depends_on: step.depends_on!.filter((parent) => parent in renamed).map((parent) => renamed[parent]) }));
  return next;
}

export type PinDirection = "in" | "out";
export function pinConnections(steps: Step[], id: string, direction: PinDirection): Array<{ from: string; to: string }> {
  const dependencies = operationDependencies(steps);
  if (!dependencies[id]) return [];
  return direction === "in" ? dependencies[id].map((from) => ({ from, to: id }))
    : Object.entries(dependencies).filter(([, parents]) => parents.includes(id)).map(([to]) => ({ from: id, to }));
}
export function breakPinConnections(result: InterfacePlannerResult, id: string, direction: PinDirection): InterfacePlannerResult {
  const next = materializeDependencies(result);
  if (!next.plan.steps.some((step) => step.step_id === id)) throw new Error("Select an operation pin.");
  next.plan.steps = next.plan.steps.map((step) => ({ ...step, depends_on: direction === "in" && step.step_id === id ? [] : direction === "out" ? step.depends_on!.filter((parent) => parent !== id) : step.depends_on }));
  return next;
}
export function movePinConnections(result: InterfacePlannerResult, fromPin: string, toPin: string, direction: PinDirection): InterfacePlannerResult {
  if (fromPin === toPin || !result.plan.steps.some((step) => step.step_id === toPin)) throw new Error("Drop onto a different matching pin.");
  const links = pinConnections(result.plan.steps, fromPin, direction);
  if (!links.length) throw new Error("This pin has no connections to move.");
  let next = breakPinConnections(result, fromPin, direction);
  // Work on a clone and commit only if every transferred connection is valid.
  for (const link of links) {
    const from = direction === "out" ? toPin : link.from;
    const to = direction === "in" ? toPin : link.to;
    if (operationDependencies(next.plan.steps)[to]?.includes(from)) continue;
    next = connectOperations(next, from, to);
  }
  return next;
}
