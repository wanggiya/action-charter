#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_path="$project_root/.venv/bin/python"
host="${INTERFACE_API_HOST:-127.0.0.1}"
port="${INTERFACE_API_PORT:-8765}"

if [[ ! -x "$python_path" ]]; then
  echo "Error: project virtual environment is unavailable: $python_path" >&2
  exit 2
fi

export PYTHONPATH="$project_root/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$project_root"

exec "$python_path" -c '
import inspect
import sys
from pathlib import Path
import geoagent_harness.interface_api.server as server

host, port, root = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
handler_source = inspect.getsource(server._handler)
route = "/api/v1/plans/save-reviewed-recipe"
print(f"Interface API source: {server.__file__}", flush=True)
print(f"Planner recipe-save route occurrences: {handler_source.count(route)}", flush=True)
print(f"Listening on http://{host}:{port}", flush=True)
server.serve_interface_api(project_root=root, host=host, port=port)
' "$host" "$port" "$project_root"
