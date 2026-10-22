# Learning ability without model training or RL

Direction recorded 2026-10-21. Proposed progression; not a claim that every layer
below is implemented. The operator allows RL to take longer, but still requires
an evaluated learning ability before demo/real-data acceptance. Do not treat this
as permission to remove existing capability/private-memory gates.

## Definition and current evidence

For this project, useful learning means later compatible tasks benefit from
retained verified experience: less user effort, fewer incorrect proposals or
shorter completion time, without carrying execution authority forward. It does
not require modifying Ollama model weights or adding an LLM agent.

Existing pieces: reusable recipes, successful-method retrieval and optional
own-chat operation check counts/ranking. The latter uses a fixed scoring rule,
not an RL policy or trained predictor. A Critic annotation or workflow summary
is advice, not deterministic proof of correct processing. Read-only completion
without independent checks adds no positive validation reward. Experimental
method-helper notes are machine-generated advice, not reliable domain facts.
The prior paired model evaluation did not demonstrate general ranking benefit;
keep that feature optional OFF and preserve its negative/inconclusive results.

## Candidate progression, in dependency order

| Approach | What is retained and how it helps | Cost / limitation |
|---|---|---|
| Case-based recipe reuse | Verified operation sequence and compatible parameter roles; retrieve and rebind for a new task | Low compute; old success does not prove compatibility or correctness on new data |
| Failure feedback | Stable error class and relevant contract/schema conditions suggest a bounded correction or unsupported scope | No training; avoid brittle sentence-specific rules and never memoize operational authority |
| Context-aware retrieval | Rank compatible cases using operation contracts, column/type roles, CRS/units and request terms | Lightweight SQLite indexes can suffice initially; keyword similarity alone cannot establish semantic suitability |
| Private domain notes | Scoped, source-backed facts with applicability, version/date, corrections and expiry | Addresses knowledge recall rather than executable skill; requires provenance and separate privacy/acceptance work |
| Small supervised ranker | Learn to rank already-eligible cases/strategies from labeled fixture outcomes | CPU-feasible in principle; needs enough representative labels, held-out evaluation and rollback |
| Contextual bandit, later | Adapt bounded strategy selection from verified outcomes and measured costs | An RL-family alternative, not a synonym for fixed scoring; exploration belongs in isolated fixtures first |
| Model fine-tuning, later | Train model parameters from curated demonstrations | More data/compute and deployment complexity; separate from retrieval and not the first laptop implementation |

Recommendation: first make case-based reuse and failure feedback reliable and
measurable, then add schema/context-aware retrieval. A learned ranker is optional
until enough evidence exists. Do not add a new agent or model call for every
lookup. Planner interprets meaning and selects methods; deterministic services
filter incompatible candidates and bind mechanical details; Critic can annotate
recorded evidence. Independent checks determine verified success.

## Proposed shared structure

    terminal runs + deterministic checks
        → bounded experience records, keyed by current contract and context
        → eligible-case retrieval / optional ranking
        → short advisory methods supplied to Planner
        → normal typed proposal → validation → exact execution controls

Experience should store method/contract identity, bounded schema roles, evidence
references and typed failure classes. Avoid raw rows, credentials and indiscriminate
transcript copying. Stay within one chat initially. Missing/invalid/expired or
changed-contract records fall back to ordinary planning. No automatic installation,
write-policy changes, approval reuse, retries or execution are implied.

A method can say “group sales by region and sum amount,” but cannot silently
assume that a new column uses the same units, a join key is unique or a new CRS
is compatible. Uncertain semantic mappings must ask a concrete question. Domain
facts and executable recipes are different records with different validation.

## Acceptance before calling it useful learning

Use existing isolated evaluation infrastructure; deferred external-harness research
is not needed. Freeze a baseline and fixture tasks before tuning. Include changed
schemas/values, held-out task variants, incompatible contracts and known failures.
Compare learning OFF/ON with identical model settings and repeated trials. Measure
verified task completion, corrections/calls/tokens, latency and user interventions.
Separate model time from processing time and disclose unsuccessful trials.

Require a predeclared useful benefit without correctness or authorization
regressions. Experience persistence, recall and reset must work across restart;
no cross-chat disclosure or unsupported operation may result. If evidence is
insufficient, report “experience retention/reuse implemented, improvement unproven”
instead of claiming learning success. Do not train or enable a policy to hide
remaining deterministic execution defects.

## Checkpoint placement

28.2: finish explicit inspection submission and reliable outcome accounting;
then evaluate existing case reuse/feedback and a focused context-aware retrieval
slice. A genuine adaptive policy can follow that foundation; weight training is
not required. 28.3 visualization and 29 private domain knowledge retain their
existing acceptance work. Cross-chat sharing remains 30+ and separately authorized.
This document designs alternatives; it does not implement a new learning model,
feedback store, retrieval schema or supervised ranker.

## Domain knowledge and transferable methods

[Recorded design](DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md) separates sourced domain knowledge, dataset definitions, habits, recipes and executable capabilities. Planner applies knowledge; Critic proposes lessons; backend services enforce provenance, applicability, correction and retrieval. Capture/reuse should make later work require less repeated input. This is proposed, not delivered learning; cross-chat use remains behind the existing later decision gate.

## Checkpoint-28 evaluation decision — 2026-10-22

Existing own-chat successful-method retrieval and optional check-outcome ranking
were exercised through fixed temporary workflows. In the new two-repetition,
six-case local-model comparison, OFF and ON each completed 10/12 attempts with
14 calls; both failed the same vector task twice. A focused schema correction
then passed the four vector retests (2/2 per side, one call/task). Preserve the
original failure report and do not merge different code versions into a new
24/24 result. [Exact metrics and limitations](CHECKPOINT28_CLOSEOUT.md).

No recommendation reliability/call-count benefit is established: keep ranking
optional/OFF. The comparison retains successful-method retrieval in both sides;
it does not isolate all memory benefits. Negative check feedback, invalid stores,
changed contracts, isolation and reset have deterministic acceptance tests;
improved arbitrary failure recovery/domain recall is unproven. This is an
evaluated experimental feature, not model training, RL or a cleared broader
learning/demo gate. Checkpoint 29 retains private sourced knowledge/corrections;
cross-chat 30+ and adaptive policies remain separately gated.
