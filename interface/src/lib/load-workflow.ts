import { workflowSchema, type Workflow } from "./workflow";

const MAX_PROJECTION_BYTES = 250_000;

export async function loadWorkflowProjection(fallback: Workflow): Promise<Workflow> {
  try {
    const response = await fetch("/runtime/workflow.json", { cache: "no-store", credentials: "same-origin" });
    if (!response.ok) return fallback;
    const declaredLength = Number(response.headers.get("content-length") ?? "0");
    if (declaredLength > MAX_PROJECTION_BYTES) return fallback;
    const text = await response.text();
    if (new TextEncoder().encode(text).byteLength > MAX_PROJECTION_BYTES) return fallback;
    return workflowSchema.parse(JSON.parse(text));
  } catch {
    return fallback;
  }
}
