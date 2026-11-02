# Checkpoint 18 — reproducible local startup

Checkpoint 18 replaces the two-terminal development sequence with one
repository-owned launcher while preserving ActionCharter's authority boundary.

## Start

Install the project and pinned frontend dependencies once, then run:

```bash
make interface-start
```

The equivalent direct command is:

```bash
bash scripts/start_actioncharter.sh
```

The API and frontend bind to `127.0.0.1`. One `Ctrl+C` stops both. Run the
launcher from any directory; it resolves the repository from its own path.
The frontend runs the already installed Vite executable directly, allowing the
launcher to wait for and terminate the real server process.

## Authority modes

Default startup exports `ENABLE_WRITE_TOOLS=false` and
`ALLOW_OVERWRITE=false`. Planning, inventories, previews, and other read-only
work remain available, but recipe execution is blocked.

Existing bounded, separately approved recipe execution requires a deliberate
local opt-in:

```bash
bash scripts/start_actioncharter.sh --enable-write-tools
```

Overwrite remains disabled. The option does not grant arbitrary shell, SQL,
Python, filesystem, network, Docker, GeoServer, or Snakemake authority.

## Diagnostics

Run prerequisite and optional-service checks without starting services:

```bash
make interface-check
```

Missing `.venv`, Node, Corepack, frontend dependencies, API imports, or free
ports are startup errors with corrective guidance. Ollama, Docker, PostGIS, and
GeoServer are capability-specific: their absence is reported but does not
prevent unrelated interface work. Credentials are never printed.

The launcher does not install packages, start containers, or alter external
services. PostGIS and GeoServer remain externally managed Docker services;
Ollama may remain on Windows and use the configured loopback URL.

## Validation

```bash
bash -n scripts/start_actioncharter.sh
.venv/bin/pytest tests/test_interface_launcher.py
make test
make interface-validate
make validate
```

`make test` remains the Python/offline boundary. `make interface-validate`
performs the TypeScript check and production build. `make validate` combines
those checks with launcher syntax and the Compose contract. The project will
add `pnpm test` only when executable frontend component/API-client tests exist.

Reference-environment acceptance must additionally prove:

1. `make interface-check` passes without starting services.
2. Default `make interface-start` reports execution authority disabled.
3. `curl http://127.0.0.1:8765/api/v1/health` reports
   `execution_authority: false`.
4. One `Ctrl+C` stops the frontend and API without a Python traceback.
5. Starting with an occupied port fails without leaving either child alive.
6. `--enable-write-tools` changes only the bounded execution flag; overwrite
   remains false.

Ubuntu 24.04 under WSL2 is the reference development environment. The CLI
remains the supported automation, diagnosis, and recovery path.

## Alpha-release gate

An alpha tag is created only after WSL2 acceptance and required protected-main
checks pass. Release notes must state the local-only trust boundary, supported
PostGIS vertical slice, advanced-interface complexity, and known production
limitations.
