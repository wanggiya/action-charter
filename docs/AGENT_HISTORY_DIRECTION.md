> Cross-chat memory is explicitly deferred until checkpoint 30 or later. [Decision and acceptance](DEFERRED_CROSS_CHAT_MEMORY.md). Current UI uses Saved chat history and Context sent to Planner, not a generated-memory collection.

> Current direction: [one conversation = one task](CHECKPOINT26_CONVERSATIONS.md), with private transcript/plan memory. Topic changes retain context. Cross-chat linking/sharing is disabled; semantic summaries and core memory remain proposed.

# Conversation memory and proposed summaries

The expanded [project memory architecture](PROJECT_MEMORY_ARCHITECTURE.md) records versioned core/optional memory, curator corrections and methods. The operator authorized incremental work: [26.1 conversation memory](CHECKPOINT26_CONVERSATIONS.md) now keeps each chat private using local SQLite. Other memory features remain design proposals; laptop resource constraints remain.

## Existing implementation

Legacy Planner records are project-local JSON in `planner-conversations/`; explicitly task-adopted conversations use `planner-workspace/tasks.sqlite3`.
The interface lists and reopens conversations with their persisted messages, selected skills,
revision and latest validated proposal. The selector uses task titles for adopted conversations or the first user message truncated to 120 characters for legacy chats; neither is an agent-generated summary. Model context uses
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
