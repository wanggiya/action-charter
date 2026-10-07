# Documentation cleanup acceptance

This change reorganizes onboarding and current context without changing execution code. Earlier README and status remain in labelled development snapshots; detailed status history is also restored beneath the current overview in CURRENT_STATUS. Existing checkpoint documents retain their names and historical content; they are not automatically all rewritten or guaranteed current by this change.

## Check locally

```bash
make inspect
make test
```

Open the root README in GitHub/VS Code Markdown preview. Confirm both Mermaid diagrams render, their labels contain no checkpoint numbers, setup shows the combined launcher, and capability limits distinguish existing recipe execution from the newer Intent bridge. Follow the documentation/context indexes and check their local links. Inspect interface/README.md for frontend-specific instructions.

No frontend feature was added: no new browser action is required. If using the Planner, restart the API after unzipping because PROJECT_SUMMARY and CURRENT_STATUS are prompt inputs. Model wording may vary with the shorter context; deterministic policy remains unchanged. A live Planner test can use: `Create exactly one step using inspect_vector with path data/input/sample_points.geojson. Plan only.` Check the actual returned scope rather than expecting identical text.

27 focused Planner/integration cases and links in the rewritten current guides were checked during preparation. Full local tests remain the operator's acceptance step. Existing historical checkpoints and roadmap are intentionally retained for traceability.

The next product work remains the task-centered conversation/graph/run journey, not more incremental paragraphs in the README. Keep that implementation's user-facing changes reflected here and in the current guides.
