import { workflowCatalogSchema, workflowSchema, type Workflow, type WorkflowSummary } from "./workflow";

const MAX_PROJECTION_BYTES = 250_000;

async function boundedJson(path: string): Promise<unknown> {
  const response = await fetch(path, { cache: "no-store", credentials: "same-origin" });
  if (!response.ok) throw new Error("runtime projection unavailable");
  const declaredLength = Number(response.headers.get("content-length") ?? "0");
  if (declaredLength > MAX_PROJECTION_BYTES) throw new Error("runtime projection is too large");
  const text = await response.text();
  if (new TextEncoder().encode(text).byteLength > MAX_PROJECTION_BYTES) throw new Error("runtime projection is too large");
  return JSON.parse(text);
}

export async function loadWorkflowProjection(fallback: Workflow, taskId?: string): Promise<Workflow> {
  const safeId = taskId && /^[a-z0-9][a-z0-9_-]{0,80}$/.test(taskId) ? taskId : undefined;
  try {
    return workflowSchema.parse(await boundedJson(safeId ? `/runtime/${safeId}.json` : "/runtime/workflow.json"));
  } catch (error) {
    if (safeId) throw new Error("selected runtime projection is unavailable or invalid", { cause: error });
    return fallback;
  }
}

export async function loadWorkflowCatalog(): Promise<WorkflowSummary[]> {
  try { return workflowCatalogSchema.parse(await boundedJson("/runtime/catalog.json")).workflows; }
  catch { return []; }
}
