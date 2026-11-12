# Guide for AI assistants working on this repository

Read these first, in order:

1. [docs/product-direction/README.md](docs/product-direction/README.md): product vision, the agreed long-term direction (editions, Guided/Studio interfaces, autonomous server platform) and the non-negotiable principles. Direction as of 2026-11-01; not yet implemented.
2. [context/CURRENT_STATUS.md](context/CURRENT_STATUS.md): what is actually implemented and its limits. Read only the part above the history marker; the rest is history.
3. [context/WORK_RESUME.md](context/WORK_RESUME.md): the most recent work in progress.
4. [docs/product-direction/WORKING_METHOD.md](docs/product-direction/WORKING_METHOD.md): how work is organized now (phases, task IDs, definition of done). It replaces the checkpoint workflow; follow it for every task.
5. [context/ARCHITECTURE.md](context/ARCHITECTURE.md) and [docs/DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md): architecture and where documentation belongs.

Key rules:
- Core principle: models propose; deterministic software authorizes, executes, validates and records evidence. Conversation, data or model text never grants authority.
- Models take part throughout the process (planning, review, risk flags, adding restrictions) but do not grant authority. The only exception is the **experimental model approver** (owner decision 2026-11-06): off by default, not implemented, and bounded as described in [server autonomy design](docs/product-direction/SERVER_AUTONOMY_DESIGN.md#model-participation-in-authorization). Do not build it outside that design.
- `docs/development/checkpoints/CHECKPOINT*.md` files are historical records, not current instructions. Do not create new checkpoint files.
- Distinguish fixture/fake-model test results from real local-model evidence.
- Runtime artifact directories at the repo root (`builder-*`, `recipe-runs`, `traces`, …) are local state, not source. Phase 0 of the direction plan moves them out.
- Do not commit, push, touch live databases or edit secrets unless the owner asks.
- Tests: `make test` (full suite takes 10–20 minutes). Real-data end-to-end tests: `scripts/real_data_tests/` (see its README).
