# Remote Development from Android

ActionCharter's full development workflow assumes Linux, Python 3.11 or newer,
and Docker Compose v2. On Android, use the phone as the editor and terminal
client while a remote Linux environment performs installation, tests, and
container work.

The recommended setup is GitHub Codespaces in a mobile browser. Termux is a
useful secondary SSH and Git client, but native Termux is not a supported full
ActionCharter runtime.

## Recommended: GitHub Codespaces

The repository includes `.devcontainer/devcontainer.json`. It creates a Python
3.11 Debian-based development container, installs Docker Compose access, builds
the project virtual environment with `make install`, and configures VS Code to
use `.venv`.

The development container receives access to the Codespaces host Docker daemon
so that repository Compose contracts can be exercised. That socket is a
developer capability, not an ActionCharter runtime trust boundary: do not run
unreviewed containers or scripts in the Codespace.

The small `.devcontainer/Dockerfile` removes an unused Yarn package source from
the upstream image before Dev Container features are installed. ActionCharter
does not use Node.js or Yarn; this prevents an unrelated Yarn signing-key
failure from blocking Docker feature installation.

### Start from an Android phone

1. Open the ActionCharter repository in Chrome or another modern browser.
2. Select **Code**, then **Codespaces**, then **Create codespace on main**.
3. Choose the smallest two-core machine for routine documentation, Python, and
   focused-test work.
4. Wait for the `postCreateCommand` to finish. The first creation installs the
   Python and GIS development dependencies.
5. Create a branch before editing:

   ```bash
   git switch main
   git pull --ff-only origin main
   git switch -c <branch-name>
   ```

6. Confirm the environment:

   ```bash
   .venv/bin/python --version
   docker version
   docker compose version
   .venv/bin/python -m pip check
   ```

### Phone-friendly validation

Use the least expensive check that covers the change:

```bash
# One focused test module
.venv/bin/pytest -q tests/<test_module>.py

# Read-only public fixture inspection
make inspect

# Deterministic pilot readiness gate
make checkpoint14f-readiness

# Full offline regression
make test

# Compose configuration without starting the system
make config
```

Run `make build` only when container definitions or runtime dependencies
changed. Building all images takes more time, storage, and Codespaces compute
than documentation or focused Python work.

### Commit and push

```bash
git status --short
git diff --check
git add <reviewed-files>
git commit -m "<type>: <summary>"
git push -u origin HEAD
```

Open a pull request from the pushed branch. Use a regular merge commit after CI
passes; do not squash unless the project's merge policy is explicitly changed.

### Control cost

- Use a two-core codespace by default.
- Set a short personal idle timeout, such as 10 or 15 minutes.
- Explicitly stop the codespace after each session; closing the browser tab is
  not the same as stopping compute.
- Delete abandoned codespaces so they stop consuming storage allowance.
- Add a hard Codespaces budget before enabling paid overage.
- Avoid prebuilds until repeated setup time justifies their Actions and storage
  usage.

## Termux as a remote client

Termux is useful when a terminal is easier than the browser editor. Use it to
connect to a remote Linux host; do not treat its Android userland as equivalent
to the Ubuntu/WSL2 and container environment used by the project.

Install only the client tools from the same trusted Termux distribution source:

```bash
pkg update
pkg install git openssh
```

Then connect to a Linux VM or another development host:

```bash
ssh <user>@<remote-host>
```

Run Git, Python, pytest, Docker, and PostGIS operations on that remote host. Do
not copy `.env`, PostGIS passwords, private datasets, approval packages, or
runtime evidence into general Android shared storage.

## Native Termux scope

Native Termux can still be useful for:

- reading and editing Markdown;
- reviewing diffs;
- lightweight Git operations; and
- dependency-free Python changes that will be validated remotely.

It is not currently a supported environment for:

- the complete GeoPandas, GDAL, rasterio, and pyogrio dependency set;
- Docker Compose runtime-boundary validation;
- the full PostGIS promotion and rollback demonstration;
- container security-contract tests; or
- authoritative execution using project credentials and evidence.

PRs created from a phone remain subject to the same focused tests, full offline
regression, container checks where relevant, CI review, and regular-merge policy
as laptop development.

## Model and database limitations

The default local model URL targets Ollama on the developer's local host. A
Codespace cannot automatically reach an Ollama server running inside a laptop's
WSL environment. Model-backed workflows therefore require a deliberately
secured reachable endpoint or should remain on the laptop.

Offline tests, deterministic policy work, documentation, read-only fixture
checks, and most repository development do not require Ollama or PostGIS.
Never expose a local model, PostGIS service, or credential solely to make it
reachable from a phone or Codespace.

## Rebuild or recover

When `.devcontainer/devcontainer.json` changes, use **Codespaces: Rebuild
Container** from the command palette. If dependency installation failed, retry:

```bash
make install
.venv/bin/python -m pip check
```

Keep work committed or pushed to a branch before deleting or rebuilding a
codespace.
