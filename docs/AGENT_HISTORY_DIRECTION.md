# Agent history and summaries — proposed, not implemented

## Existing implementation

Planner conversation records are project-local JSON in `planner-conversations/`.
The interface lists and reopens conversations with their persisted messages, selected skills,
revision and latest validated proposal. The selector's current "summary" is the first user
message truncated to 120 characters, not an agent-generated summary. Model context uses
bounded transcript excerpts and the current workflow; the history switch excludes previous
messages without deleting the saved transcript. Context-usage counts expose omissions.
There is no unified cross-agent history or automatically maintained semantic summary.
Execution attempts/evidence remain separate authoritative records.

## Options for the next checkpoint

| Approach | Advantages | Costs / limitations |
| --- | --- | --- |
| Persist full transcript + bounded recent excerpts (current) | Easy to audit and reopen; bounded prompts; no summary model call | Old constraints can fall outside the prompt; first-message label describes later revisions poorly |
| Rolling generated summary plus recent turns | Retains earlier intent in a smaller prompt; readable session overview | Summaries may omit or distort constraints; extra latency; must preserve original messages and source references |
| Structured event history with deterministic digest/status summaries | Reliable proposal/approval/run links; accurate failures and recovery state | Does not capture all conversational nuance; needs a shared event schema and agent correlation IDs |
| Retrieved older messages and evidence | Relevant long-term context without replaying everything | Retrieval can miss information; requires indexing, explicit provenance and privacy controls |

Proposed direction: retain the original transcript; introduce a correlated event timeline and
a deterministic run/session overview first. Add optional bounded semantic summaries with
source turn IDs, covered revision and explicit stale state. Treat retrieved text and summaries
as planning context only. No history, summary or old approval grants execution authority.

## Checkpoint 26 acceptance proposal

Reopen a multi-agent/session history after restart, identify proposal revisions and failed
steps, and distinguish actual execution evidence from model commentary. A summary links
back to the original messages; changing the transcript revision marks it stale. History-off
continues to exclude transcript/summary context. Recovery never repeats a write automatically
or reuses expired/mismatched authority. Implementation awaits the next checkpoint.
