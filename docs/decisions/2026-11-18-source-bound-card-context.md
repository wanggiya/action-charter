# Source-bound Data Card context and reuse

P2-D2, [issue #101](https://github.com/wanggiya/action-charter/issues/101).

## Context

D1 projects bounded facts from existing readers. A recorded digest identifies a
past read; it does not prove that a file, worksheet or filtered population is still
the intended input. Repeating metadata preparation wastes work, while filename or
mtime matching can silently reuse stale facts. Opening saved results must stay pure.

## Decision

Keep DataCard facts separate from CardUse request receipts. Reuse requires a fresh
full source/package digest, exact source/selection/read scope and a reader contract
including projection revision, Python and relevant dependency versions. Existing
bounded workers perform checks; no model decides whether content matches.

Store at most256 bounded cards in the existing workspace metadata repository.
Conversation IDs isolate chats; explicit CLI/MCP discovery has a separate namespace.
Only reconstructible cache entries may be evicted. Saved history, claims, approvals
and knowledge records are untouched. No cross-chat memory or domain learning.

Explicit positive inspection-planning requests resolve named sources or a unique
current-workflow input. Missing/ambiguous inputs ask a concrete question; unsafe
paths receive an explicit deterministic policy refusal. Database and recorded-result
questions do not silently select a local input. Inspect-on-send retains preliminary
read limits; workbook/record selection and analytical profiles need reviewed Execute
in the interface. CLI/MCP explicit discovery uses the same service via opt-in context
mode. Model/conversation text never enables a read gate or grants write authority.

## Consequences and limits

This adds two shared modules and extends existing contracts/adapters; no new agent,
container, processing operation or arbitrary library execution. Models receive facts
and propose work; Executor and Critic keep existing responsibilities. Last-send
receipts are displayed in the existing context disclosure. Refresh, saved-chat reads
and disclosure expansion never check current bytes or call a model.

Full hashing still costs I/O and does not freeze the source after checking. A sample
with a complete digest is still a sample, not a full statistical profile. Changed
reader/runtime contracts require preparation again. Two synthetic local4B observations
both produced valid proposals; candidate context/tokens increased. No efficiency,
reliability or domain-analysis improvement is established by a single pair. Source
routing/runtime/prompt/read-gate hardening after capture is fixture-tested, not a new
model trial.

[Behavior, transport options and acceptance](../DATA_CARDS.md#source-selection-and-lifecycle-p2-d2).
