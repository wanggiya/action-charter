# Skills before code; Phase 2 targets

Date: 2026-11-18. Decided by the project owner.

Context: Phase 1 benchmark (B5, real qwen3.5:9b): 8 passed, 11 failed, 4 timeouts of
27. The owner asked why know-how is not added as agent skills instead of new code.

Decision:
- Agent skills (instruction files the model reads) are a first-class way to add
  know-how. Code is written only for new abilities, guarantees, or speed/reliability
  the benchmark shows a skill alone cannot reach. Skills never grant authority and may
  reference only registered operations. New task P2-K.
- Phase 2 targets versus B5 on suite v1: at least 15/27 passing without correctness
  regressions; timeouts at least halved; median task under 60 s; diabetes hero journey
  4 of 5 runs; traceable plain-language report; safety tasks end in clear refusals.
- Added Phase 2 tasks: P2-0 identity check after WSL device change (first), P2-S
  small-cell suppression, P2-H2 county health map, P2-E2 CAD import (DWG converter
  decision pending).

Details: [PHASE_2_PLAN.md](../product-direction/PHASE_2_PLAN.md).
