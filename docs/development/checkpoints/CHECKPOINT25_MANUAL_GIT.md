# Manual Git handoff

These are operator instructions. The assistant has not staged, committed, pushed, created a PR or merged.
Run from the project root. Preserve and review your existing changes before selecting files.

```bash
git status --short
git switch -c checkpoint25-library-discovery
git diff
```

Review tracked changes interactively; select only the changes you want in this checkpoint:

```bash
git add -p
```

The following new source/documentation paths belong to this checkpoint. Review their contents before adding:

```bash
git add docs/development/checkpoints/CHECKPOINT25.md docs/AGENT_HISTORY_DIRECTION.md docs/OUTPUT_VISUALIZATION_DIRECTION.md docs/development/checkpoints/CHECKPOINT25_MANUAL_GIT.md examples/README.md examples/checkpoint25/ interface/src/components/OperationFlow.tsx interface/src/components/OperationsPanel.tsx interface/src/lib/operations-api.ts src/geoagent_harness/operations/ tests/test_operation_discovery.py scripts/checkpoint25_browser_check.mjs scripts/setup_browser_tests.sh
```

Inspect staged filenames and the actual diff. Do not include `.env`, `.secrets`, credentials,
ZIP/download archives, private data, `library-discovery/`, `operation-packages/`, outputs,
conversation/attempt records, or private browser/audio downloads. This handoff is not a new
secret audit of your staged selection.

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached
make test
make interface-validate
git commit -m "Add governed library discovery and installed operation contracts"
git push -u origin checkpoint25-library-discovery
gh pr create --base main --head checkpoint25-library-discovery --title "Checkpoint 25: governed library discovery and extensions" --body "Adds shared operation contracts, persistent static library discovery, a tested data-only adapter, readable dataflow cards and functional examples. Validated with backend tests, frontend checks and an isolated browser workflow. Discovery and installation grant no execution authority."
gh pr checks --watch
```

After reviewing the PR and passing checks, merge using a merge commit:

```bash
gh pr merge --merge
git switch main
git pull --ff-only
```

If the branch name already exists, use a new descriptive name consistently in the branch,
push and PR commands. Do not publish a release as part of this checkpoint.
