# Roadmap history and preservation record

P0-7, 2026-11-04, [issue #64](https://github.com/wanggiya/action-charter/issues/64).
Current priorities live in the [active roadmap](../../context/PRODUCT_ROADMAP.md).
This index and the snapshot preserve earlier requirements and rationale, not execution
permission, a new checkpoint sequence or proof of implementation.

## Preservation

- Original: `context/PRODUCT_ROADMAP.md`, **113,332 bytes**.
- Original SHA-256: `87a71a11e57c29669a1fc43c95271912d5b0a3aabf697f4239241a877c679c8e`.
- [Snapshot](PRODUCT_ROADMAP_BEFORE_P0_7.md) retains the entire original text in its
  original order after `<!-- original-roadmap-body -->`. Only the **94 relative
  Markdown link destinations** are rebased to preserve navigation from this directory.
- Preservation is checked by reading the snapshot body, resolving each relative link
  from its new directory and expressing it relative to `context/`, then comparing its
  UTF-8 bytes and SHA-256 with the original. Headings, paragraphs, tables, code blocks,
  inline paths, statuses and unresolved alternatives are not rewritten.
- Old contradictions and deadlines stay visible as history. Use WORKING_METHOD for
  current order, CURRENT_STATUS for implementation and WORK_RESUME for the handoff.
- No original requirements are discarded because a newer phase plan exists. Detailed
  specifications stay at their existing paths; no new checkpoint document is created.

## Requirement coverage

Historical-content limit: the pre-existing `checkpoints/CHECKPOINT24.md` currently
contains CI YAML rather than the former conversation-context heading. It is not
rewritten here; recovering its intended historical content requires separate review.
The README's stale anchor now points to current Planner guidance. Link checks verify
paths/fragments, not the scientific or historical correctness of every linked record.

| Original family | Current navigation / retained detail |
|---|---|
| Real-data F1–F5, T01–T15, statistics, reports, formats, role modes and database transfer | [Active requirement map](../../context/PRODUCT_ROADMAP.md#retained-requirements-and-design-links), [full-data acceptance](../FULL_DATA_WORKFLOW_ACCEPTANCE.md), [T checklist](../IMPLEMENTATION_TODO.md#ordered-work-items-and-acceptance) |
| Inspection, graph/Outcome, history, CLI and bounded worker delivery | [Current implementation](../../context/CURRENT_STATUS.md), original delivery sections below and their linked acceptance guides |
| Acquisition, learning/RL, private domain knowledge, A/B memory and sharing | [Deferred/open decisions](../../context/PRODUCT_ROADMAP.md#deferred-commitments-and-open-decisions), original proposals below; no new sharing/training authority |
| Spatial contracts, agent identity, release lineage, Snakemake, PostGIS and GeoServer | Original foundation, skill strategy and historical 14–23 sections below; broader typed service requirements remain T13 |
| Presentation, pilot, public examples, package/open-source/release requirements | Original presentation/release sections below and [active phase sequence](../../context/PRODUCT_ROADMAP.md#dependency-ordered-delivery); old dates are not launch commitments |
| Earlier schedules, incomplete alternatives and acceptance numbers | Entire snapshot preserved; these do not override later owner decisions or current task status |

## Verification

Documentation audit: 14 files, 545 local Markdown links and 151 Markdown fragments
checked with no missing destinations; snapshot reconstruction matches all 113,332
original bytes and the SHA-256 above. The active roadmap (under 15,000 bytes) passes both its
64,000-byte maintenance target and the actual 128,000-byte bounded reader. Twelve
context-pack tests passed in 1.02 s. Final full `make test`, completed 2026-11-05:
**2,483 passed**, 13 existing spatial warnings, 682.93 s (11:22). No frontend/runtime
code changed in this task, so frontend/browser checks were not repeated. This is
automated fixture evidence, not a new real-local-model or live-service acceptance.

To repeat the preservation check from the repository root, without a temporary backup:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib, os, re

archive = Path('docs/development/PRODUCT_ROADMAP_BEFORE_P0_7.md')
original_dir = Path('context')
body = archive.read_text().split('<!-- original-roadmap-body -->\n\n', 1)[1]
pattern = re.compile(r'(!?\[[^\]\n]*\]\()([^\s)]+)(\))')

def restore(match):
    url = urlsplit(match[2])
    if url.scheme or url.netloc or not url.path:
        return match[0]
    target = os.path.relpath(archive.parent / unquote(url.path), original_dir)
    if url.query:
        target += '?' + url.query
    if url.fragment:
        target += '#' + url.fragment
    return match[1] + target + match[3]

data = pattern.sub(restore, body).encode('utf-8')
assert len(data) == 113332
assert hashlib.sha256(data).hexdigest() == '87a71a11e57c29669a1fc43c95271912d5b0a3aabf697f4239241a877c679c8e'
assert Path('context/PRODUCT_ROADMAP.md').stat().st_size < 64000
print('Preservation and active-roadmap size: passed')
PY
```

## Original section index

The snapshot begins with dated 2026-10-27 through 2026-11-01 delivery/requirement
notes before its first section. [Start at the original opening](PRODUCT_ROADMAP_BEFORE_P0_7.md#actioncharter-product-roadmap)
for those F/T-series links and the original introduction. Remaining sections follow
in original order:

- [Outcome page, field details and terminal charts — 2026-10-26](PRODUCT_ROADMAP_BEFORE_P0_7.md#outcome-page-field-details-and-terminal-charts--2026-10-26)
- [Persistent terminal and chat workflow history — implemented, 2026-10-25](PRODUCT_ROADMAP_BEFORE_P0_7.md#persistent-terminal-and-chat-workflow-history--implemented-2026-10-25)
- [Interactive analytical selection — 2026-10-25](PRODUCT_ROADMAP_BEFORE_P0_7.md#interactive-analytical-selection--2026-10-25)
- [Frontend/CLI continuity — implemented slice, 2026-10-25](PRODUCT_ROADMAP_BEFORE_P0_7.md#frontendcli-continuity--implemented-slice-2026-10-25)
- [Next acceptance journey — post-inspection data science and engineering](PRODUCT_ROADMAP_BEFORE_P0_7.md#next-acceptance-journey--post-inspection-data-science-and-engineering)
- [Implemented 2026-10-25 — comprehensive inspection and Docker runtime](PRODUCT_ROADMAP_BEFORE_P0_7.md#implemented-2026-10-25--comprehensive-inspection-and-docker-runtime)
- [Latest agreed delivery — complete real-data inspection journey](PRODUCT_ROADMAP_BEFORE_P0_7.md#latest-agreed-delivery--complete-real-data-inspection-journey)
- [Proposed next slice — Executor-managed Docker worker and typed inspection](PRODUCT_ROADMAP_BEFORE_P0_7.md#proposed-next-slice--executor-managed-docker-worker-and-typed-inspection)
- [Latest integration — analytical evidence in graph and inspector](PRODUCT_ROADMAP_BEFORE_P0_7.md#latest-integration--analytical-evidence-in-graph-and-inspector)
- [Latest slice — bounded analytical conversation, 2026-10-25](PRODUCT_ROADMAP_BEFORE_P0_7.md#latest-slice--bounded-analytical-conversation-2026-10-25)
- [Current priority — real-data frontend retest](PRODUCT_ROADMAP_BEFORE_P0_7.md#current-priority--real-data-frontend-retest)
- [Checkpoint 29 — preserved working proposal](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-29--preserved-working-proposal)
- [Checkpoint 28 revised consolidation target — 2026-10-22](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-28-revised-consolidation-target--2026-10-22)
- [Checkpoint 28.1 bounded acquisition pilot — 2026-10-20](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-281-bounded-acquisition-pilot--2026-10-20)
- [Post-calculation delivery clarification](PRODUCT_ROADMAP_BEFORE_P0_7.md#post-calculation-delivery-clarification)
- [Runtime writes and pre-demo gate — planned](PRODUCT_ROADMAP_BEFORE_P0_7.md#runtime-writes-and-pre-demo-gate--planned)
- [Optional capability acquisition — decision recorded 2026-10-19](PRODUCT_ROADMAP_BEFORE_P0_7.md#optional-capability-acquisition--decision-recorded-2026-10-19)
- [Immediate priority](PRODUCT_ROADMAP_BEFORE_P0_7.md#immediate-priority)
- [Checkpoint 27 — technical acceptance; operator validation next](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-27--technical-acceptance-operator-validation-next)
- [Bounded-calculation extension — implemented slice](PRODUCT_ROADMAP_BEFORE_P0_7.md#bounded-calculation-extension--implemented-slice)
- [Checkpoint 26 operational delivery order](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-26-operational-delivery-order)
- [Dependency-ordered checkpoints 24–27](PRODUCT_ROADMAP_BEFORE_P0_7.md#dependency-ordered-checkpoints-2427)
- [28.3 — Visualization expansion before representative demo acceptance](PRODUCT_ROADMAP_BEFORE_P0_7.md#283--visualization-expansion-before-representative-demo-acceptance)
- [Cross-chat memory deferred: checkpoint 30 or later](PRODUCT_ROADMAP_BEFORE_P0_7.md#cross-chat-memory-deferred-checkpoint-30-or-later)
- [Product direction](PRODUCT_ROADMAP_BEFORE_P0_7.md#product-direction)
- [Existing foundation](PRODUCT_ROADMAP_BEFORE_P0_7.md#existing-foundation)
- [Presentation target](PRODUCT_ROADMAP_BEFORE_P0_7.md#presentation-target)
- [Checkpoint 14B — Isolated Builder agent](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-14b--isolated-builder-agent)
- [Checkpoint 14C — Spatial data contracts and benchmark](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-14c--spatial-data-contracts-and-benchmark)
- [Checkpoint 14D — Agent identity and operational history](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-14d--agent-identity-and-operational-history)
- [Checkpoint 14E — Authoritative results and release packages](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-14e--authoritative-results-and-release-packages)
- [Checkpoint 14F — Pilot-ready demonstration](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-14f--pilot-ready-demonstration)
- [Checkpoint 15 — Expanded PostGIS workflows and controlled release](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-15--expanded-postgis-workflows-and-controlled-release)
- [Candidate future directions](PRODUCT_ROADMAP_BEFORE_P0_7.md#candidate-future-directions)
- [Candidate — Restricted GeoServer publication](PRODUCT_ROADMAP_BEFORE_P0_7.md#candidate--restricted-geoserver-publication)
- [Candidate — Guided product interface and Snakemake productization](PRODUCT_ROADMAP_BEFORE_P0_7.md#candidate--guided-product-interface-and-snakemake-productization)
- [Candidate — Pilot operations and bounded memory](PRODUCT_ROADMAP_BEFORE_P0_7.md#candidate--pilot-operations-and-bounded-memory)
- [Skill strategy](PRODUCT_ROADMAP_BEFORE_P0_7.md#skill-strategy)
- [Open-source direction](PRODUCT_ROADMAP_BEFORE_P0_7.md#open-source-direction)
- [Priority before the presentation](PRODUCT_ROADMAP_BEFORE_P0_7.md#priority-before-the-presentation)
- [Prototype release definition](PRODUCT_ROADMAP_BEFORE_P0_7.md#prototype-release-definition)
- [Checkpoint 15: controlled PostGIS operations](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-15-controlled-postgis-operations)
- [Checkpoint 16B — governed activation of an existing GeoServer layer](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-16b--governed-activation-of-an-existing-geoserver-layer)
- [Checkpoint 17L — CLI/interface parity baseline](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17l--cliinterface-parity-baseline)
- [Checkpoint 17M — loopback proposal compilation](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17m--loopback-proposal-compilation)
- [Checkpoint 17N — digest-bound reviewed recipe storage](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17n--digest-bound-reviewed-recipe-storage)
- [Checkpoint 17O — stored recipe inventory](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17o--stored-recipe-inventory)
- [Checkpoint 17P — exact approval-request preparation](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17p--exact-approval-request-preparation)
- [Checkpoint 17Q — append-only recipe approval decision](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17q--append-only-recipe-approval-decision)
- [Checkpoint 17R — independent recipe approval verification](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17r--independent-recipe-approval-verification)
- [Checkpoint 17S — exact execution preview](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17s--exact-execution-preview)
- [Checkpoint 17T — first governed interface execution](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17t--first-governed-interface-execution)
- [Checkpoint 17U — live execution state and recovery](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17u--live-execution-state-and-recovery)
- [Checkpoint 17V — durable attempt inventory and graph restoration](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17v--durable-attempt-inventory-and-graph-restoration)
- [Checkpoint 17W — Planner Agent interface entry point](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17w--planner-agent-interface-entry-point)
- [Checkpoint 17X — reviewed Planner-result storage](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17x--reviewed-planner-result-storage)
- [Checkpoint 17Y — exact plan-approval preparation](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17y--exact-plan-approval-preparation)
- [Checkpoint 17Z — append-only plan decision](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17z--append-only-plan-decision)
- [Checkpoint 17AA — plan-decision inspection and verification](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17aa--plan-decision-inspection-and-verification)
- [Checkpoint 17AB — Planner execution-envelope preview](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ab--planner-execution-envelope-preview)
- [Checkpoint 17AC — restart-safe plan restoration](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ac--restart-safe-plan-restoration)
- [Checkpoint 17AD — verified plan to governed recipe candidate](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ad--verified-plan-to-governed-recipe-candidate)
- [Checkpoint 17AE — reviewed Planner recipe storage](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ae--reviewed-planner-recipe-storage)
- [Checkpoint 17AF — exact stored-recipe approval handoff](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17af--exact-stored-recipe-approval-handoff)
- [Checkpoint 17AM — rooted interface data paths](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17am--rooted-interface-data-paths)
- [Checkpoint 17AN — governed resource selection](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17an--governed-resource-selection)
- [Checkpoint 17AO — actionable Planner rejection](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ao--actionable-planner-rejection)
- [Checkpoint 17AP — responsive Planner authoring](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ap--responsive-planner-authoring)
- [Checkpoint 17AQ — deterministic Critic assurance](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17aq--deterministic-critic-assurance)
- [Checkpoint 17AR — recipe-run trace adaptation preview](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ar--recipe-run-trace-adaptation-preview)
- [Checkpoint 17AS — reviewed adapted-trace persistence](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17as--reviewed-adapted-trace-persistence)
- [Checkpoint 17AT — explicit read-only Critic assessment](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17at--explicit-read-only-critic-assessment)
- [Checkpoint 17AU — immutable Critic-result recording](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17au--immutable-critic-result-recording)
- [Checkpoint 17AV — governed recipe release](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17av--governed-recipe-release)
- [Checkpoint 17AW — governed Snakemake export](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17aw--governed-snakemake-export)
- [Checkpoint 17AX — guided prototype closure](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ax--guided-prototype-closure)
- [Checkpoint 17AY — complete PostGIS interface vertical slice](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-17ay--complete-postgis-interface-vertical-slice)
- [Checkpoint 18 — reproducible local startup](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-18--reproducible-local-startup)
- [Checkpoint 19 — simplified default workspace](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-19--simplified-default-workspace)
- [Checkpoint 20 — automatic authority-chain projection](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-20--automatic-authority-chain-projection)
- [Checkpoint 21 — governed task history](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-21--governed-task-history)
- [Checkpoint 22 — reviewed context and intent reasoning](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22--reviewed-context-and-intent-reasoning)
- [Checkpoint 23 — task-centered agent interface](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-23--task-centered-agent-interface)
- [Checkpoints 24–27](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoints-2427)
- [Checkpoint 22C — Intent reasoning](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22c--intent-reasoning)
- [Checkpoint 22D — Intent clarification API](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22d--intent-clarification-api)
- [Checkpoint 22E — resolved Intent review](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22e--resolved-intent-review)
- [Checkpoint 22F — reviewed Planner handoff](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22f--reviewed-planner-handoff)
- [Checkpoint 22G — Intent review/handoff API](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22g--intent-reviewhandoff-api)
- [Checkpoint 22H — Context & intent interface](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22h--context--intent-interface)
- [Checkpoint 22I implementation](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22i-implementation)
- [Checkpoint 22J — saved-review recovery](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22j--saved-review-recovery)
- [Checkpoint 22K — focused task stages](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22k--focused-task-stages)
- [Checkpoint 22L — fresh tasks](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22l--fresh-tasks)
- [Checkpoint 22M — inspection envelopes](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22m--inspection-envelopes)
- [Checkpoint 22N and Checkpoint 23 scope](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-22n-and-checkpoint-23-scope)
- [Checkpoint 25 operator follow-up and next delivery slices](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-25-operator-follow-up-and-next-delivery-slices)
- [28.2 implementation slice](PRODUCT_ROADMAP_BEFORE_P0_7.md#282-implementation-slice)
- [Proposed 28.2 follow-up — inspection on send](PRODUCT_ROADMAP_BEFORE_P0_7.md#proposed-282-follow-up--inspection-on-send)
- [Deferred harness and specialization research — 2026-10-21](PRODUCT_ROADMAP_BEFORE_P0_7.md#deferred-harness-and-specialization-research--2026-10-21)
- [28.2 bounded inspection submission delivered — 2026-10-21](PRODUCT_ROADMAP_BEFORE_P0_7.md#282-bounded-inspection-submission-delivered--2026-10-21)
- [Operator clarification — inspection is format-independent (2026-10-21)](PRODUCT_ROADMAP_BEFORE_P0_7.md#operator-clarification--inspection-is-format-independent-2026-10-21)
- [28.3 first result-exploration slice — 2026-10-21](PRODUCT_ROADMAP_BEFORE_P0_7.md#283-first-result-exploration-slice--2026-10-21)
- [Domain knowledge acquisition direction — recorded 2026-10-21](PRODUCT_ROADMAP_BEFORE_P0_7.md#domain-knowledge-acquisition-direction--recorded-2026-10-21)
- [28.2 single-dataset inspection expansion — implementation](PRODUCT_ROADMAP_BEFORE_P0_7.md#282-single-dataset-inspection-expansion--implementation)
- [28.3 vector-first spatial views](PRODUCT_ROADMAP_BEFORE_P0_7.md#283-vector-first-spatial-views)
- [Characteristics-first spatial discovery — 2026-10-22](PRODUCT_ROADMAP_BEFORE_P0_7.md#characteristics-first-spatial-discovery--2026-10-22)
- [Checkpoint 28 closeout — 2026-10-22](PRODUCT_ROADMAP_BEFORE_P0_7.md#checkpoint-28-closeout--2026-10-22)
