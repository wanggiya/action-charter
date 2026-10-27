#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_context="$(mktemp -d /tmp/actioncharter-worker-build-XXXXXX)"
trap 'rm -rf -- "$build_context"' EXIT
for package in discovery tabular sandbox; do mkdir -p "$build_context/geoagent_harness/$package"; done
for file in __init__.py discovery/__init__.py discovery/source.py discovery/csv.py tabular/__init__.py tabular/dataset_profile.py sandbox/__init__.py sandbox/worker.py; do
  cp -- "$project_root/src/geoagent_harness/$file" "$build_context/geoagent_harness/$file"
done
cp -- "$project_root/docker/analytical-worker/Dockerfile" "$build_context/Dockerfile"
docker build --pull=false --network=none -t actioncharter-analytical-worker:local "$build_context"
