# Documentation

Start with the [project README](../README.md) for installation, scope and the execution model.

## Operators

- [Repeatable interface acceptance and bug triage](INTERFACE_ACCEPTANCE.md)
- [Core concepts: skills, recipes and workflows](CORE_CONCEPTS.md)
- [Interface/CLI coverage](INTERFACE_CLI_PARITY.md)
- [Interface scope](INTERFACE_PRODUCT_SCOPE.md)
- [WSL frontend setup](WSL_FRONTEND_SETUP.md)
- [API troubleshooting](INTERFACE_API_TROUBLESHOOTING.md)
- [Local model troubleshooting](MODEL_TROUBLESHOOTING.md)
- [Remote development](REMOTE_DEVELOPMENT.md)
- [Security](../SECURITY.md)

## Contributors and maintainers

- [Contributing](../CONTRIBUTING.md)
- [Documentation responsibilities](DOCUMENTATION_GUIDE.md)
- [Product direction 2026-11: vision, editions/interfaces, autonomous platform design](product-direction/README.md)
- [Architecture](../context/ARCHITECTURE.md)
- [Current status](../context/CURRENT_STATUS.md)
- [Product roadmap](../context/PRODUCT_ROADMAP.md)
- [Interface design direction](INTERFACE_DESIGN_DIRECTION.md)

## Development records

[development/checkpoints/](development/checkpoints/) holds the CHECKPOINT*.md files, which describe historical delivery and acceptance. They are retained for traceability; consult [current status](../context/CURRENT_STATUS.md) and the [phase/task working method](product-direction/WORKING_METHOD.md) before following old setup instructions. New work does not create more checkpoint files.

[Roadmap history](development/ROADMAP_HISTORY.md) indexes the complete pre-P0-7 roadmap, including earlier priorities, alternatives and requirements. The [active roadmap](../context/PRODUCT_ROADMAP.md) links current dependencies and remaining design work.

[Previous README](development/README_BEFORE_REORGANIZATION.md) and [previous status](development/STATUS_BEFORE_REORGANIZATION.md) are preserved historical snapshots, not current guidance.

- [Planner dialogue frontend acceptance](PLANNER_DIALOGUE_ACCEPTANCE.md): current source launcher, conversation revisions/recovery, compact graph controls and separately reviewed PostGIS test.

- [Frontend vector-to-PostGIS walkthrough](FRONTEND_VECTOR_POSTGIS_WALKTHROUGH.md): exact messages, arguments, separate authorization/execution, evidence and recovery checks.

- [Main-workflow Snakemake blocks](WORKFLOW_SNAKEMAKE_BLOCKS.md): Add/Planner, completed-run reuse, exact export permission and static package verification.

- [Checkpoint 23 review](development/checkpoints/CHECKPOINT23_REVIEW.md): complete change scope, why it changed and remaining browser/review gates before commit/push.

- [Checkpoint 23 browser regression](development/checkpoints/CHECKPOINT23_BROWSER_CHECK.md): fixture-only Chromium checks, measured layout/drag regressions and repeatable test setup.
