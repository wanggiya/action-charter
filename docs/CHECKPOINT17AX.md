# Checkpoint 17AX — guided prototype closure

Checkpoint 17 closes with a working governed interface path from request and
data selection through planning, approval, execution, validation, evidence,
Critic review, immutable release, and reproducible Snakemake export.

Repeated export of the same recipe digest is idempotent. The service validates
the existing package again and reports `EXISTING EXPORT · CONTRACT VALID`
instead of presenting an inconspicuous duplicate error.

The interface response contract accepts both valid export outcomes: a newly
created package reports `export_performed: true`, while revalidation of an
existing package reports `export_performed: false`. Both outcomes require a
passing static contract and never execute the workflow or recipe.

## Deliberate boundary

Snakemake dry-run and replay remain available through the isolated
`workflow-runner` Compose service and CLI. The loopback web API is not granted
Docker socket, arbitrary subprocess, shell, SQL, or package-install authority.
Checkpoint 18 may expose replay after unified local service orchestration can
preserve explicit approval, progress, cancellation, and evidence boundaries.

## Prototype-release handoff

After merging 17AX, prepare the first prototype release from clean `main`:

```bash
git switch main
git pull --ff-only origin main
make test
cd interface && pnpm typecheck && pnpm build && cd ..
docker compose --profile agents --profile tools config --quiet
```

Create a versioned release branch and tag only after required GitHub checks
pass. Release notes should describe the supported demonstration, local-only
trust boundary, known advanced-UX complexity, and Checkpoint 18 plan.
