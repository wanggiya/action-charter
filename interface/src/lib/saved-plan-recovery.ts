import type { SavedPlanInventory } from "./interface-api";
export function recoverableSavedPlan(plans: SavedPlanInventory["plans"], remembered: string | null, conversation: string | undefined) {
  return plans.find(plan=>plan.plan_sha256===remembered) ?? plans.find(plan=>plan.plan_sha256===conversation);
}
export function canRestorePlan(active:boolean, sameConversation:boolean, hasCurrentPlan:boolean, editsPending:boolean) {
  return active && sameConversation && !hasCurrentPlan && !editsPending;
}
