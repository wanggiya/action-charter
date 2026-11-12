#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_context="$(mktemp -d /tmp/actioncharter-worker-build-XXXXXX)"
trap 'rm -rf -- "$build_context"' EXIT
for file in __init__.py contracts/__init__.py contracts/paths.py contracts/table_sources.py data/__init__.py data/discovery/__init__.py data/discovery/source.py data/discovery/csv.py data/tabular/__init__.py data/tabular/field_guidance.py data/tabular/dataset_profile.py workspaces/__init__.py workspaces/sandbox/__init__.py workspaces/sandbox/worker.py; do
  mkdir -p -- "$build_context/geoagent_harness/$(dirname -- "$file")"
  cp -- "$project_root/src/geoagent_harness/$file" "$build_context/geoagent_harness/$file"
done
cp -- "$project_root/docker/analytical-worker/Dockerfile" "$build_context/Dockerfile"
docker build --pull=false --network=none -t actioncharter-analytical-worker:local "$build_context"
