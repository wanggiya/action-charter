# Checkpoint 27 technical acceptance — 2026-10-20

The bounded checkpoint 27 implementation is ready for operator interface acceptance.
This closes the implemented retention/reuse, advisory-note, Results, graph-layout
and runtime-write-control work; **27.6 installation/package work remains explicitly
sequenced after the capability/learning/memory gates and chosen-data/demo acceptance**.
This is a local alpha acceptance record, not release readiness or product parity.

## Automated verification

- `make test`: **1,825 passed**. Temporary fixtures; no live database changes.
- `make interface-validate`: typecheck and production build passed. The existing
  large-chunk warning remains (about 704 KB uncompressed main JS); no bundle-size
  or cross-platform performance claim is made.
- Browser journeys use the actual shared backend, disposable files and separate
  Chromium profiles. Models are fixtures in these journeys, not actual inference.
  Results/layout 14, inspector visualization 10, calculations 12, write policy 5,
  Critic graph 7 and recipe/cancellation/recovery 6 cases passed: **54 cases**.
- Scope includes changed-artifact refusal, literal HTML-like values, signed-chart
  boundaries, full-versus-sampled sums, polygons/holes/attributes, persisted dragging,
  repeated insertion, vertical layout, stale authority, cancellation and restart.

User visual judgment and the manual interface exercise below remain operator work.
No fresh installation, Windows/macOS packaging, real-data or live-PostGIS acceptance
is implied. No staging, commit, push, merge or publication was performed.

## Actual configured-model profile

A separate service-level driver uses real local Ollama inference and synthetic
spatial, tabular and combined files in a disposable project. It uses the same
conversation, validation, authorization, execution, retention and retrieval services
as the interface/CLI, with explicit fixture-only authorization. The existing
launcher configuration was not modified.

Runtime: Linux x86_64, 16 logical CPUs as reported by the test runtime. Host GPU,
physical memory/power and isolated hardware performance were not measured. Some
development checks ran concurrently: timings are observations, not a benchmark
against another product or a controlled speed comparison.

- Model: `qwen3:4b-instruct`, installed digest
  `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
- Planner: 120-second request setting, 1,024 output tokens, JSON-schema decoding,
  `reasoning_effort=none`; no model installation or weight training.
- Final profile: **6/6 valid proposals and correct executions**, all retained.
- Reuse fixtures change amount values and point coordinates; assertions verify
  the new source paths, attribute-to-CSV reference, computed values and geometry.
- All three reuse requests automatically received a prior own-chat method example.
  Empty model reuse-citation lists are not interpreted as an explicit reuse claim.
- **13 model calls: 7 Planner calls and 6 optional Critic calls**. CSV reuse needed
  one bounded Planner correction. No Planner timeout in this final profile.
- All six Critic requests timed out at the explicit 15-second bound. This verifies
  fail-soft execution/retention, **not reliable live Critic enrichment** on this
  setup. Available-note indexing/provenance is fixture-tested separately.

| Domain | Phase | Planner seconds | Planner calls | Total seconds including optional assessment | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Spatial inspection | Initial | 23.10 | 1 | 38.82 | Correct |
| Spatial inspection | Changed input | 23.49 | 1 | 39.19 | Correct; method retrieved |
| CSV calculation | Initial | 22.14 | 1 | 37.99 | Correct |
| CSV calculation | Changed input | 78.91 | 2 | 94.90 | Correct after one correction; method retrieved |
| Spatial attributes → grouped CSV | Initial | 43.99 | 1 | 60.55 | Correct |
| Spatial attributes → grouped CSV | Changed input | 64.99 | 1 | 80.90 | Correct; method retrieved |

Total observed time was 352.34 seconds. Scripted trials needed no interactive
operator clarification; the script intentionally supplies exact authorization for
its disposable fixture outputs. This does not remove human review/authorization
from normal use or count developer fixes between profiles as zero effort.
The observed spatial plans also repeated a read-only inspection; correctness is
not evidence that plans are minimal or optimally efficient.

A six-case sample does not establish broad reliability. Semantic completeness for
arbitrary natural language, live Critic quality and model latency remain limitations.
There is no measured manual baseline or demonstrated Tableau/Google/Databricks/
KNIME/Ansible parity or speedup.

## Earlier development profiles — failures retained

These profiles used changing code, settings and validation strength. They are not
an A/B experiment, a model ranking or interchangeable reliability samples. Earlier
reuse fixtures did not include the final changed-value/source-binding assertions.
All were synthetic; rejected proposals and refused overwrites were not successes.

| Profile | Model / timeout / tokens | Correct executions / attempts | Model calls | Model timeouts | Main observations |
| --- | --- | ---: | ---: | ---: | --- |
| Initial | 9B / 90s / 2048 | 4/6 | 12 | 0 | Combined selection omitted a required available prerequisite; invalid proposals rejected |
| Dependency closure | 9B / 90s / 2048 | 1/2 | 3 | 1 | Redundant source question; one combined execution completed |
| Source grounding | 9B / 90s / 2048 | 0/2 | 3 | 1 | Timeout and missing same-source inspection dependency |
| Smaller-model comparison | 4B / 90s / 2048 | 2/6 | 8 | 2 | Omitted requested inspection; repeated known-source questions |
| Typed spatial sequence | 9B / 90s / 2048 | 1/2 | 3 | 2 | One Planner timeout; a complete combined execution succeeded |
| Saved settings, before final fixes | 4B / 120s / 1024 | 3/6 | 9 | 4 | CSV omission/timeout; combined repeat refused an occupied output without overwrite |
| Final acceptance | 4B / 120s / 1024 | 6/6 | 13 | 6 | Correct changed-source/value execution; timeouts confined to optional Critic |

9B is `qwen3.5:9b`, digest
`6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`;
4B is the installed model identified above. Generic unavailable Critic responses
must not be called timeouts unless the call metrics establish a timeout.

Fixes prompted by these observations: registry prerequisite closure, safe supplied
source references, removal of irrelevant missing-file examples, narrow explicit
inspection/calculation coverage, typed simple spatial sequencing, and occupied-CSV
proposal correction. None relax authority, install generated code or rerun a write automatically.
Semantic arguments still come from the proposal; trusted services allocate
omitted mechanical output paths and bind required gates before review. Snapshot/rendering and backend validation remain independent
of model descriptions.

## Reproduction and operator acceptance

Run the service evaluation separately from the launcher if desired:

```bash
.venv/bin/python scripts/checkpoint27_model_evaluation.py --model qwen3:4b-instruct --timeout 120 --max-tokens 1024 --output /tmp/actioncharter-checkpoint27-acceptance.json
```

The report contains every attempt, prompt, safe metrics, current-source checks and
retrieval receipts. `--domain spatial|tabular|combined` selects a smaller evaluation;
use a different output filename to preserve earlier reports. Calls are sequential;
only temporary fixture outputs receive the script's authorization. Temporary data
is removed; reports remain in `/tmp`, outside Git and normal browser caches.

For interface acceptance, use [synthetic visualization fixtures](../examples/visualization/README.md):
inspect CSV, check region sums and pie/donut, click chart marks and dismiss their details by outside click/Escape, inspect boundaries/holes/attributes,
move tool/outcome blocks and refresh, insert/discard blocks, and inspect shared
warning write controls. Run a fresh calculation through review/authorization and
check doubled values and evidence. Existing snapshots do not acquire new geometry.
The assistant supplies the exact click-by-click sequence in the conversation.

## What follows before real-data/demo/publication

1. **28.1 optional capability acquisition:** one bounded generated adapter family,
   isolated temporary/held-out/negative tests, explicit promotion and independent
   runtime authorization; default OFF, existing operations first.
2. **28.2 learning/RL pilot:** opt-in evidence-based choice of eligible recipes and
   planning strategies, bounded experiments and a measured baseline. It must not
   update Ollama weights implicitly or weaken execution rules.
3. **28.3 visualization expansion:** renderer-library evaluation, grouped/stacked
   charts/heatmaps, temporal axes, multiple map layers, declared-CRS handling,
   style/legends, optional basemaps and bounded recorded database-geometry support;
   then linked filters/dashboards/export and appropriate raster/large-data support.
   Planner-driven visualization specifications remain future work; current view
   controls are operator-selected. Validate the supported subset needed by the demo.
4. **29 private domain memory:** source-linked field knowledge, corrections and
   expiration, bounded retrieval and recall/isolation tests within a conversation.
   Cross-chat sharing remains 30+ and needs a fresh operator decision.
5. Operator-selected real-data workflows and demo acceptance, with separate explicit
   permission for live services. Then deferred **27.6 installable-package/release
   preparation**, clean-install/restart/user-data preservation checks and only
   explicitly approved publication. This document publishes nothing.
