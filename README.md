# GeoAgent Skill Harness

A CLI-first, local-first scaffold for containerized geospatial agent workflows.
It targets Ubuntu WSL development with:

- one Ollama runtime on the laptop;
- three independent logical-agent containers;
- one isolated GIS/MCP-tools container; and
- one existing, separately managed PostGIS container.

Checkpoint 1 implements only the deterministic `inspect_vector` skill. It does
not yet call Ollama, expose MCP transport, load PostGIS, or generate reports.

## Checkpoint 1 boundary

Implemented:

- GeoJSON, GeoPackage, and Shapefile inspection;
- canonical path enforcement beneath `data/input`;
- typed JSON output with driver, layers, CRS, geometry type, feature count,
  fields, and extent;
- Typer CLI, sample data, and pytest coverage;
- independent planner, executor, and critic container definitions;
- a shared lightweight agent image without GIS libraries or model weights;
- external-network configuration for an existing PostGIS container;
- host Ollama endpoint configuration;
- an isolated GIS-tools image;
- GitHub Actions, Makefile, `.dockerignore`, and security policy.

Not implemented: Ollama calls, agent loop, live MCP server, conversion, database
loading, database validation, approvals, trace writing, and report generation.
Unimplemented modules fail closed rather than pretending those features exist.

## Repository tree

```text
.github/workflows/      tests and container build checks
agents/                 role and permission manifests
context/                concise project state and decisions
data/input/             read-only source datasets
data/output/            generated artifacts only
docker/agent/           one image used by three independent containers
docker/gis-tools/       isolated GDAL/Python/MCP runtime
skills/                 human-readable skill contracts
src/geoagent_harness/   installable Python package
tests/                  automated tests
traces/                 future JSONL execution traces
reports/                future Markdown reports
```

## Install under Ubuntu WSL

Keep the repository in the Linux filesystem, such as `~/projects`, rather than
developing directly under `/mnt/c` or `/mnt/e`.

```bash
sudo apt update
sudo apt install -y git make curl jq unzip python3 python3-venv python3-pip

mkdir -p ~/projects
cd ~/projects
```

If your browser saves the archive in Windows Downloads:

```bash
unzip /mnt/c/Users/YOUR_WINDOWS_USERNAME/Downloads/geoagent-skill-harness-wsl-checkpoint-1.zip
cd geoagent-skill-harness
```

If you copied the archive into `~/Downloads`:

```bash
unzip ~/Downloads/geoagent-skill-harness-wsl-checkpoint-1.zip
cd geoagent-skill-harness
```

## Local Python verification

```bash
make install
make inspect
make test
```

Direct equivalent:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/geoagent inspect-vector data/input/sample_points.geojson --pretty
.venv/bin/pytest
```

## Existing PostGIS container

This repository does not create, stop, or own PostGIS. Create a shared network
and attach the existing PostGIS container once:

```bash
docker network create geoagent-backend

docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Networks}}"

docker network connect \
  --alias postgis \
  geoagent-backend \
  YOUR_EXISTING_POSTGIS_CONTAINER
```

If Docker reports that the network or connection already exists, inspect it:

```bash
docker network inspect geoagent-backend
```

## Ollama and containers

Ollama runs once on the laptop. The future agents will use its
OpenAI-compatible endpoint at `host.docker.internal`; model weights are never
copied into agent images.

```bash
curl http://localhost:11434/api/tags

cp .env.example .env
# Edit POSTGRES_* and MODEL_NAME. Never commit .env.

make config
make build
make agent-info
```

`make agent-info` starts each independent agent image, validates its manifest,
prints a redacted description, and exits. It intentionally reports
`agent-loop-not-implemented`.

Run the implemented GIS skill inside its container:

```bash
docker compose --profile tools run --rm mcp-gis \
  geoagent inspect-vector data/input/sample_points.geojson --pretty
```

Checkpoint 1 does not connect to PostGIS. Database configuration is included
for the later loader and verifier and must never enter model prompts or traces.

## Expected inspection result

The exact CRS text and field dtypes can vary slightly by GDAL version:

```json
{
  "source": "data/input/sample_points.geojson",
  "driver": "GeoJSON",
  "layers": [{
    "name": "sample_points",
    "crs": "EPSG:4326",
    "geometry_type": "Point",
    "feature_count": 2,
    "fields": [
      {"name": "id", "type": "int32"},
      {"name": "name", "type": "object"}
    ],
    "extent": {
      "min_x": -71.0589,
      "min_y": 42.3601,
      "max_x": -71.0567,
      "max_y": 42.3612
    }
  }]
}
```

## Manual verification before GitHub

1. Run `make inspect`; confirm it finds two Point features.
2. Run `.venv/bin/geoagent inspect-vector README.md`; confirm rejection because
   the file is outside `data/input`.
3. Put a text file under `data/input`; confirm its extension is rejected.
4. Run `make test`.
5. Run `make config`, `make build`, and `make agent-info`.
6. Optionally compare with
   `ogrinfo -so -al data/input/sample_points.geojson`.
7. Run `git status --ignored`; ensure `.env`, real data, outputs, traces,
   reports, models, and database storage will not be committed.

## First GitHub commit

```bash
git init
git branch -M main
git add .
git status
git diff --cached --check
git commit -m "feat: scaffold GeoAgent skill harness"
```

Review `git status` carefully. Choose and add a license before making the
repository public; this scaffold intentionally does not choose one for you.

## Security

No skill accepts a command string or invokes a shell. Canonical path checks
reject traversal and symlink escapes. Compose uses read-only agent filesystems,
read-only inputs, narrow output mounts, dropped Linux capabilities, and
`no-new-privileges`.

See `SECURITY.md` for trust boundaries and prototype limitations.

## Known limitations

- Shapefile inspection needs its sidecar files and reports one layer.
- Driver-specific field dtypes are not normalized to a universal ontology.
- Encoding, Z/M dimensions, and per-feature validity are not checked.
- Agent containers validate manifests only and do not call Ollama.
- MCP transport and PostGIS access are not implemented.
- Compose isolation is not a complete host egress firewall.
- The existing PostGIS lifecycle remains outside this repository.
- No command is claimed to have run on the user's WSL installation.

