# Checkpoint 18 plan — reproducible local product startup

Checkpoint 18 begins by turning the accepted guided prototype into something a
new operator can start reliably. It does not add model, database, package
installation, replay, or browser execution authority.

## Outcome

From a clean supported checkout, one documented command starts the loopback
interface API and frontend, reports available optional services, and shuts both
down cleanly with one `Ctrl+C`.

The existing CLI remains supported for automation, diagnosis, and recovery.

## Supported environment

- Ubuntu 24.04 under WSL2 is the reference development environment.
- Python runs from the project `.venv`.
- Node and pnpm versions remain pinned by repository metadata.
- Ollama may run on Windows and be reached through its configured loopback URL.
- PostGIS and GeoServer remain externally managed Docker services.

## Required behavior

1. Add one repository-owned launcher for frontend and interface API.
2. Resolve the project root independently of the caller's current directory.
3. Validate `.venv`, Node, pnpm, interface dependencies, required directories,
   configured ports, and imported API source before startup.
4. Detect Ollama, Docker, PostGIS, and GeoServer availability without printing
   secrets or treating unavailable optional capabilities as universal failure.
5. Explain the exact unavailable capability and corrective action.
6. Default to `ENABLE_WRITE_TOOLS=false` and `ALLOW_OVERWRITE=false`.
7. Require an explicit launcher option for write-enabled local execution.
8. Bind both services to loopback unless the operator explicitly chooses an
   independently documented remote-development mode.
9. Prefix or otherwise distinguish frontend and API diagnostics.
10. Forward termination, wait for both children, and exit without a Python
    traceback after one `Ctrl+C`.
11. Fail if either child exits unexpectedly and terminate the remaining child.
12. Keep generated dependencies, builds, logs, PIDs, and runtime evidence out
    of Git.

## Explicit non-goals

- No Docker-socket access for the browser API.
- No automatic package installation.
- No automatic database or GeoServer mutation.
- No arbitrary shell, SQL, Python, filesystem, or network tool.
- No Snakemake replay from the browser.
- No Pandas capability expansion yet.
- No hidden approval or automatic acceptance of model output.

## Validation

- Start from the repository root and from an unrelated working directory.
- Confirm one command starts both services and the browser can reach the API.
- Confirm default startup keeps execution disabled.
- Confirm the explicit write option is visible and deliberate.
- Confirm missing Ollama, Docker, or PostGIS produces bounded diagnostics.
- Confirm occupied ports fail clearly without orphan processes.
- Confirm one `Ctrl+C` stops both processes with exit code zero.
- Run the complete Python suite, frontend typecheck/build, Compose contract,
  and shell static checks.

## Prototype release gate

After Checkpoint 18 passes, create the first documented alpha release from protected
`main`. Release notes must state the local-only trust boundary, reference WSL2
environment, supported end-to-end PostGIS demonstration, advanced-interface
complexity, and known production limitations.
