# Checkpoint 22 closeout

## Delivered

Checked historical retrieval and immutable context review; reasoning-only Intent with clarification; history-free tasks; immutable Intent review and recovery; exact vector/raster metadata plan handoff and plan storage; continuation into existing Plan review. Historical denial never authorizes new work. CLI remains supported.

The offline integration matrix covers 12 vector/raster, fresh/history and decision combinations. Its model is a fixture: it does not establish live Ollama quality or browser usability. Earlier local live checks are operator evidence, not a substitute for the checks below.

## Remaining boundaries

- Intent supports one metadata inspection input, not arbitrary write workflows.
- A read-only plan with no approval-required steps cannot yet use the legacy approval-dependent recipe compiler. Stop at stored plan; Checkpoint 23 must join this safely. Never fabricate approval.
- Textual input in Intent does not automatically select a file picker item.
- Refresh clears unsaved drafts. Stored reviews/plans can be recovered with source checks.
- This is checked history retrieval, not generalized long-term memory or autonomous execution.

## Local acceptance

From the project root:

```bash
make test
make interface-validate
bash scripts/start_actioncharter.sh
```

In Context & intent: Start without history; request `Inspect data/input/sample_points.geojson and return feature count, fields and CRS only. Read-only inspection.` Review the actual proposal, confirm that reading is allowed and writes/database loading are prohibited, then store reviewed Intent. Select Vector metadata, generate the inspection plan and check exactly one inspect_vector step with the correct path and validation_required=false. Store it and Continue in Plan. A conservative requires_approval=true flag is retained, never silently cleared.

Refresh and recover the stored Intent from saved reviews. It should reopen the Plan stage without another model call. A historical-context test must retain denial and reject changed sources. Follow CHECKPOINT22N.md for the full matrix and raster example.

## Commit and PR

This ZIP is cumulative. Unzip into the existing checkout; it does not replace your local secrets or Docker configuration. First inspect your branch and changes:

```bash
git status --short --branch
git diff --check
```

If on main, create a branch before committing (do not pull over uncommitted work):

```bash
git switch -c feat/checkpoint22-context-intent
```

If already on the intended feature branch, keep it. Stage the reviewed project source, tests and documentation with VS Code Source Control. Exclude downloaded ZIPs, runtime evidence, build output, dependencies and secrets. Inspect staged changes before committing:

```bash
git diff --cached --stat
git diff --cached --check
git commit -m "feat: add checked context and reviewed intent planning"
git push -u origin HEAD
gh pr create --base main --title "Add checked context and reviewed intent planning" --body "Adds source-checked history retrieval, immutable context and intent reviews, fresh-task reasoning, vector/raster inspection handoff and recovery. Keeps execution authority separate. Validated with Python tests and frontend typecheck/build; current limits and Checkpoint 23 integration plan are documented."
gh pr checks --watch
```

Only after checks pass and the diff is reviewed:

```bash
gh pr merge --merge --delete-branch
git switch main
git pull --ff-only origin main
```

Checkpoint 22 is ready for local acceptance and PR review. These commands have not been executed on your repository by this deliverable.
