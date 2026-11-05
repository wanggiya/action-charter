# P0-7: active roadmap and preserved history

Context: the 113,332-byte roadmap mixed current priorities with checkpoint-era
delivery notes, unfinished requirements, alternatives and contradictory “next” steps.
The existing trusted-file bound is 128,000 bytes. The current context-pack builder
does not include the roadmap in its fixed file list.

Decision: keep a compact active dependency/requirement map at the existing roadmap
path. WORKING_METHOD retains task/phase order, CURRENT_STATUS implementation truth
and WORK_RESUME the immediate handoff. Preserve the entire prior roadmap in a
labelled snapshot, rebase its Markdown links and provide a section/requirement index.
Verify reconstruction against the original bytes/SHA-256. Maintain 64,000-byte
headroom for the active roadmap; do not change runtime context loading.

Consequences: requirements remain discoverable without bringing historical scheduling
into current instructions. T01–T15 and memory alternatives are retained, not newly
approved or completed. Phase 0 still requires its overall exit audit after P0-7.
No application, agent, dependency, data or authority behavior changes. See the
[active roadmap](../../context/PRODUCT_ROADMAP.md) and
[preservation record](../development/ROADMAP_HISTORY.md).
