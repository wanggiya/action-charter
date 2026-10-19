# Planner response structure and diagnostics

The conversational Planner now sends a structural Reply schema through
`response_format.type=json_schema`, rather than requesting generic JSON and relying
only on prompt text. This uses the existing model client and coordinator; it adds
no agent, MCP server, execution permission or extra retry.

[Ollama documents schema output through its OpenAI-compatible API](https://docs.ollama.com/capabilities/structured-outputs).
Endpoint support varies; a real probe of the local endpoint rejected the full
Pydantic schema with “failed to parse grammar,” but accepted the structural form.
The decoder schema keeps object/array/scalar types, references, enums/constants,
required fields and closed object shapes. It omits regexes, length/count/numeric
bounds and descriptive metadata for compatibility. Property names that happen to
match a schema keyword are preserved.

The full authoritative schema remains in the prompt and backend validators.
Patterns, limits, argument types, paths, dependencies, approval, calculation rules
and output verification are unchanged. A decoder schema is not execution
validation, domain correctness or evidence of authorization. Unknown operations,
unsafe expressions and malformed proposals still reject.

## Configuration and failure behavior

- Default `MODEL_RESPONSE_FORMAT=json_schema` applies when a caller supplies a
  response schema. Conversational Planner supplies its actual allowlisted Reply
  shape; existing model calls without a schema keep their previous JSON/text mode.
- `MODEL_RESPONSE_FORMAT=json_object` is an explicit compatibility setting for an
  endpoint without schema support. The launcher accepts it from its allowlisted
  environment/.env configuration. This does not relax backend validation.
- A schema/grammar rejection is reported as model_response_format_rejected when
  identified in a 400/422 response. There is no silent downgrade or HTTP retry.
- MODEL_MAX_TOKENS remains operator-controlled; it is not increased automatically.
- A provider finish_reason=length rejects the response, including syntactically
  valid partial-scope replies. One existing correction may request a concise full
  proposal; repeated truncation reports planner_output_truncated with explicit
  output-limit guidance. A truncated discovery response cannot dispatch a tool.
- Transport timeouts are not automatically retried. Existing whole-turn call,
  context and optional deadline budgets still apply.

## Mechanical gate requirements and smaller prompts

Mandatory requires_approval/validation_required flags are bound upward from trusted
operation contracts before the conversational proposal digest and review. Planner
may omit them; false values cannot disable required checks. True extra gates are
retained, and existing optional approval gates still cannot be silently removed.
This is requirement metadata, never an approval decision. No authority record or
CSV output is created. Manual graph/typed-workflow validation remains strict.
The receipt lists steps whose required checks were added mechanically.

The repeated recursive calculation expression union is shared once in the
model-facing schema, preserving all variants and constraints. The measured raw
schema drops from 6,062 to 2,939 serialized bytes. Simple calculation requests no
longer receive an unnecessary export schema unless export is explicitly requested
or already part of the workflow. Calculation already writes its output; an explicit
later export of transformed data must reference the producing step.

## Safe findings

An invalid whole JSON response is labelled response, not plan. A genuine plan-field
shape error separately explains that plan must be an object or JSON null, never a
quoted JSON string or list. The frontend can show response shape, finish reason,
requested response format and existing request timing/context diagnostics.
Completion-token counts and response byte size are available in the API receipt.
Unknown finish-reason values are normalized to other; raw generated text and
parser excerpts are not included in these diagnostics. A format receipt describes
what was requested, not independent proof that an endpoint honored it.

No fenced-output stripping, partial JSON acceptance, argument coercion, canned
fallback plan, extra schema-repair loop or historical authorization reuse is added.
The previous saved workflow remains intact on failure.

## Acceptance

Restart the existing launcher, refresh, and retry the same calculation request
from the [calculation guide](BOUNDED_CALCULATIONS.md). Inspect the proposed source,
formula, missing policy and output path before authorization. Planning alone must
create no output CSV. Errors now distinguish syntax, field structure, output-limit,
format compatibility and timeout cases; report the complete diagnostic if it fails.

Transport tests inspect the actual request payload, explicit compatibility mode
and no retry on rejection. Backend tests exercise malformed responses, quoted/list
plans, bounded correction, truncated discovery and saved-plan preservation. Browser
fixtures simulate one invalid JSON response before the valid proposal. Fixture
success is not proof of live-model reliability. A separate real-model planning smoke used the exact acceptance request against
local qwen3:4b-instruct with MODEL_MAX_TOKENS=1024 and reasoning effort unset.
The final run passed in one model call (51.269 seconds, 5,297 reported prompt
and 370 completion tokens), yielding inspect_csv -> calculate_csv_columns,
amount multiplied by 2 into doubled, propagate missing values, and one fresh
output target. It created no output CSV, approval or execution. Test transport
was capped at 75 seconds/call and 90 seconds/turn; production settings were not
modified. This is one planning example, not an end-to-end live-data run or a
reliability benchmark. Deterministic fixture tests separately cover execution.


Final verification: `make test` passed 1,744 tests; `make interface-validate`
passed typecheck/build; 17 browser fixture cases passed across calculation JSON
repair/edit/execute/restore (4), retained-method discovery/reuse/privacy (7) and
existing CSV workflows (6). The separate one-call real-model planning smoke is
described above and did not authorize or execute a workflow.

## Calculation argument decoding and historical omission follow-up

A read-only historical-record check found a complete-sounding calculation summary
whose actual steps contained only inspect_csv. New explicit calculated-column
requests now require that operation in any accepted non-null conversational
proposal. Omission consumes the existing single correction attempt, never an
extra retry; repeated omission preserves the previous state and reports
planner_scope_incomplete. Genuine questions and unavailable-operation explanations
remain supported. This is narrow English coverage detection, not a universal
proof of semantic completeness or formula correctness.

A local-model diagnostic then exposed a separate failure: a step supplied both
path and source_step. Calculation-focused structured output now binds argument
shapes to inspect_csv, calculate_csv_columns and export_csv skill branches.
Recursive definitions are namespaced; exclusive source choices become closed
object alternatives so the decoder cannot allow both source fields in those
branches. Automatic target paths remain optional during generation. Other
allowlisted operations retain their existing validation path and remain available.
Backend bounds, input provenance, argument types, operation gates and exact
authorization remain authoritative; decoder support is not execution permission.
The json_object compatibility mode cannot enforce these decoder shapes and still
relies on backend checks. Old saved plans are not rewritten.

Simple explicit inspection/calculation requests now receive a focused instruction
set rather than unrelated PostGIS, GeoServer, Snakemake and recipe-authoring rules.
Required-argument/approval descriptions and prelisted recipe suggestions are
focused to those detailed schemas; the operation allowlist, discovery service and
all backend checks are unchanged. The Planner manifest now explicitly permits
proposing operations that require later approval, replacing the ambiguous
“implemented and approved” wording. Its tool/filesystem/database permissions
remain disabled. These changes reduce ambiguity; they do not establish model
reliability across arbitrary workflows.

For calculation-focused decoding, non-null proposals and plan-less exchanges
use separate closed root branches. A full proposal cannot also contain a
workflow_action, recipe_uses or recipe_discovery request. Separate clarification,
authoring, assessment, composition and discovery modes remain available.

A fresh, explicit single-column calculation request (or one following a single
CSV inspection) can use a requested operation skeleton: inspection when requested
or already present, then calculation. It constrains only operation kinds/counts
through prefixItems/minItems/maxItems. It supplies no input path, formula, output
column, constant or missing policy. The model must provide those, and all backend
checks still run. Multiple creation instructions, plural derived-column requests,
negative inspection instructions, broader detailed skill scope and existing
nontrivial workflows retain the general decoder. This is a bounded request slice,
not general natural-language workflow compilation. json_object compatibility mode
cannot enforce the skeleton and still receives the backend omission check.

Final local check on 2026-10-18: qwen3:4b-instruct, 1,024 maximum output tokens,
restored temporary copy of the inspection-only historical failure, latest exact
calculation request, previous-message context OFF. It produced inspect_csv then
calculate_csv_columns with doubled = amount * 2 and missing_policy=propagate in
one call (34.44 seconds), finish_reason=stop, json_schema. Mandatory proposal
gates passed. No authorization, execution or output CSV occurred. Earlier
iterations failed on source choices, mixed reply modes and omitted operations;
those observations motivated the guards and bounded skeleton. This one passing
planning check is not broad model reliability or live execution acceptance.

Final verification of this follow-up: make test — 1,764 passed;
make interface-validate — typecheck/build passed (existing bundle-size warning);
six isolated calculation browser cases passed with the real backend and fixture
model replies. The separate actual-model planning check above passed once;
it neither executed the workflow nor replaced the operator's historical record.

## Reuse provenance constraints — 2026-10-18

A subsequent calculation failure reported “Report reuse only for an inspected/
supplied source relevant to the final workflow.” The model supplied an unverified
reused_recipe_ids claim. The failed turn preserved the historical inspection-only
workflow; the presence of a current plan or prompt example is not recipe provenance.

Before each conversational model call, root Reply schemas now constrain reuse
IDs to full successful-method examples supplied to that request and successful
recipe/method inspections from its bounded discovery session. With no eligible
sources the optional field is omitted from the closed response schema. Search
hits and prelisted catalog summaries alone cannot enable a claim. After a
successful inspection, the next model request receives the updated eligible enum,
including after correction. Recipe composition still derives its own provenance
from validated recipe_uses; it does not need a redundant explicit ID claim.

Backend provenance/relevance checks remain unchanged in strength: a supplied ID
must still relate to proposed skills and changed inspected contracts still reject.
Endpoints that ignore structured decoding receive the existing one correction
attempt; repeated claims return planner_reuse_unverified, preserve plan/transcript
and provide model-specific guidance rather than requesting extra authorization
instructions. No claim is silently stripped from a received reply. This adds no
model calls, tools, permissions, cross-chat memory or execution authority. Actual
prompt/schema size receipts now account for these per-call constraints.

The calculation browser fixture now defaults to an otherwise valid calculation
with an unsupported recipe claim on its first reply, reproducing this failure.
It verifies correction, an empty reuse receipt, visible formula, fresh approval,
actual temporary-file calculation and restoration without repeat execution.
ACTIONCHARTER_CALCULATION_FAILURE_MODE=omission or invalid_json retains the other
repair fixtures. Discovery tests separately verify search-only rejection, enum
refresh after inspection, supplied-but-unrelated sources and preserved history.

Verified follow-up: make test — 1,769 passed; make interface-validate passed
(typecheck/build; existing bundle warning); 13 isolated calculation/retention
browser cases passed. The actual qwen3:4b-instruct model also produced the correct
inspection/calculation workflow and doubled = amount * 2 with propagation in
one bounded call (52.08 seconds, 1,024-token setting), using temporary historical
context with no supplied reuse source. No authorization or execution occurred
in that model check. This remains one planning sample, not broad reliability.
