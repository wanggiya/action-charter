# Inspection source resolution and compatibility

2026-11-02 bug fix during Phase 0. No new processing operations, agents or authority.

## Observed failure

A saved follow-up `do a read-only inspection` retained sample_orders.csv but a local
model proposed inspect_vector. The CSV had not changed; the vector reader rejected it.
The workflow failed, followed by a separate optional Critic timeout. Format compatibility
was not enforced for spatial inspectors during plan validation. Storage relocation did
not cause that failure. The original failed plan/run remain historical evidence.

## Shared contract and enforcement

operations/inspection_contracts.py declares qualified inspector suffixes shared by the
operation registry, inspection source routing and validation. inspect_csv uses the existing
table-reader catalog; inspect_vector supports GeoJSON/GeoPackage/Shapefile; inspect_raster
supports TIFF. Filename qualification chooses a reader; runtime readers still validate
actual contents, source identity and resource bounds. This is not inferred domain meaning.

Plan policy, graph validation, saved-plan preparation, recipe validation and the public
recipe dispatcher reject an inspector/source mismatch. The error names the operation,
format and compatible inspector when known. It is rejected before reader dispatch rather
than replaced with an automatically rewritten saved artifact. An invalid model proposal
receives the existing one bounded correction, with the same deterministic checks afterward.

Explicit-source planning narrows descriptive inspector schemas and decoder choices. It
preserves the operation allowlist and stored capability metadata; descriptive focus is
not an authorization change. Multi-step/table/spatial workflows retain their existing
operation scope. Installed dependencies, model text and previous approvals grant no rights.

## Task-local follow-ups

Closed metadata requests such as `do a read-only inspection`, `inspect it again`, and
`repeat the inspection` use only the active workflow's declared original path/right_path
inputs. Bare names normalize under data/input. Identical inputs deduplicate; derived
output paths are not silently treated as original inputs. No transcript search, disk
search or cross-chat memory is used.

- One original source: propose its qualified inspector. Existing read-only inspect-on-send
  policy and registered skill scope still govern whether dispatch is permitted.
- Multiple plausible inputs: ask which file, preserve the workflow, dispatch nothing.
- No source/new chat: ask for a filename, never borrow another chat's source.
- Unsupported source: ask for a registered supported input; do not invent an operation.

Full-request matching prevents a mixed request such as `inspect it again and export it`
from being reduced to metadata-only work. Such requests retain normal planning/approval
requirements. Metadata paths are typed literal values, not prose reparsed for instructions.
The original user message remains in the conversation and original_request provenance.

Read-only lead-ins share the same normalizer: `do`, `run` or `perform` an inspection
`on` or `of` a named file. Full-request matching still rejects additional actions from
this shortcut. This avoids requiring the user to memorize one exact sentence; broader
language still uses the Planner model and its normal validation.

Clarification responses include the complete context-usage contract expected by the
frontend. Previously a valid filename question could be saved but rejected during UI
parsing. Opening older no-model clarification chats/receipts fills only their known
missing diagnostic fields in the response, without rewriting history or replaying work.
Zero prompt/schema/retrieval/model-time values mean no model request was made; they
are not a measurement of total submission latency. Other model diagnostics are unchanged.

A metadata-only follow-up can create a NEW compatible proposal from a legacy inspector/
format mismatch. Only that specific mismatch may bypass validation of the old context;
the new proposal is independently checked. Other invalid context remains rejected. Old
artifact bytes/digests and failed-run records are not rewritten. No write or retry authority
is inherited. The existing current-plan allowance semantics for selected skills remain.

## Validation in the interface

1. Restart the usual launcher once and refresh. Keep existing storage settings.
2. New chat: `Inspect sample_orders.csv. Return row count and column names. No writes.`
3. In that SAME chat send `do a read-only inspection`, then `inspect it again`.
   Expect Inspect CSV with data/input/sample_orders.csv, not Inspect vector.
4. With inspect-on-send OFF: review the proposal and Execute separately. With it ON:
   only existing eligible read-only metadata scope may dispatch. Optional Critic review
   is separate and may call the model; a review timeout does not invalidate completion.
5. New chat: send `inspect it again`. Expect a filename question and no workflow run.
   The question must be visible in chat without a required-field error, including after
   refresh. Then send `do a read-only inspection on sample_orders.csv.` and expect the
   CSV proposal (or eligible read-only execution when inspection-on-send is enabled).
6. With a workflow containing several original input files, send the same follow-up.
   Expect a choice question; the existing graph/history remain unchanged.
7. In a temporary plan/graph, change the CSV inspector to vector inspection. Validation
   must name the mismatch and refuse it. Do not edit immutable saved review files.

No write enable flag is required for these read-only checks. Existing failed receipts
are not retried automatically. Larger/statistical tasks retain separate contracts.

Regression tests are developer checks that previous behavior remains correct after a
change; users do not have an extra regression action. Calling an LLM instead does not
repair an API/frontend contract mismatch. Simple exact metadata requests avoid planning
inference for speed; complex requests still use the model. Both paths share deterministic
source, policy and execution validation.

## Evidence and remaining limits

2026-11-03 clarification-response fix: all **106 focused tests** passed; final
`make test`: **2,327 passed**, 13 existing spatial warnings, 621.88 seconds. Interface
validation and isolated relocated fixture browser/API/CLI/PTY passed with zero page
errors. Browser checks now require the question to render without parsing errors both
before and after refresh, then submit the owner's exact `do … inspection on …` wording.
Backend tests recreate old incomplete stored chat/receipt diagnostics, confirm readable
responses, unchanged stored values and no execution replay. An initial full run was
stopped because the sandbox blocked HTTP fixture sockets; the permitted run passed.
No live local-model call, user-data execution, database or Git mutation was performed.

Earlier source-compatibility delivery evidence follows; these counts are historical.

Tests use temporary CSV/vector/raster inputs, mocked planner replies and typed invalid
legacy fixtures. They cover source ambiguity/isolation, send policy, no replay, correction,
graph and recipe rejection, saved-artifact preservation, shared registry metadata and
literal filename handling. Browser/API/CLI tests use a temporary configured workspace,
actual metadata services and fixture model replies. These establish behavior/controls,
not general small-model reasoning quality, causality or semantic type inference.

The initial broad run exposed capability-metadata regressions; those were corrected by
narrowing decoding/descriptive contracts rather than the stored allowlist. Targeted
regressions pass. Final full suite: **2,317 passed**, 13 existing spatial warnings,
693.78 seconds. Interface validation and the relocated fixture browser/API/CLI/PTY
journey passed with zero page errors. A decoder-shape assertion was updated to require
compatible generation choices while retaining the full capability metadata. New source
tests copy only three public sample files, not the operator’s entire input directory.
No live model, database or saved user workflow was executed for this verification.
