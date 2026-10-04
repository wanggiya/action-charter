#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
api_host="127.0.0.1"
frontend_host="127.0.0.1"
api_port="${INTERFACE_API_PORT:-8765}"
frontend_port="${INTERFACE_FRONTEND_PORT:-5173}"
write_tools=false
check_only=false
api_pid=""
frontend_pid=""
stopping=false

usage() {
  cat <<'EOF'
Usage: bash scripts/start_actioncharter.sh [options]

Start the ActionCharter interface API and frontend on loopback.

Options:
  --check                 Run startup checks without starting either service.
  --enable-write-tools    Enable bounded, approval-gated recipe execution.
  --api-port PORT         Interface API port (default: 8765).
  --frontend-port PORT    Frontend port (default: 5173).
  -h, --help              Show this help.

Writes and overwrite are disabled by default. This launcher never installs
packages, starts containers, or grants arbitrary shell, SQL, or Python access.
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 2
}

status() {
  printf '[startup] %s\n' "$*"
}

is_port() {
  [[ "$1" =~ ^[0-9]+$ ]] && ((10#$1 >= 1 && 10#$1 <= 65535))
}

while (($#)); do
  case "$1" in
    --check) check_only=true; shift ;;
    --enable-write-tools) write_tools=true; shift ;;
    --api-port)
      (($# >= 2)) || die "--api-port requires a value"
      api_port="$2"; shift 2 ;;
    --frontend-port)
      (($# >= 2)) || die "--frontend-port requires a value"
      frontend_port="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

is_port "$api_port" || die "invalid API port: $api_port"
is_port "$frontend_port" || die "invalid frontend port: $frontend_port"
[[ "$api_port" != "$frontend_port" ]] || die "API and frontend ports must differ"

python_path="$project_root/.venv/bin/python"
[[ -x "$python_path" ]] || die "project virtual environment is unavailable; run make install"
command -v node >/dev/null 2>&1 || die "Node.js is unavailable; install the version declared by interface/package.json"
command -v corepack >/dev/null 2>&1 || die "Corepack is unavailable; install a supported Node.js distribution"
[[ -d "$project_root/interface/node_modules" ]] || die "frontend dependencies are unavailable; run corepack pnpm@10.17.1 --dir interface install"
[[ -x "$project_root/interface/node_modules/.bin/vite" ]] || die "Vite is unavailable in interface/node_modules; reinstall pinned frontend dependencies"

node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"
[[ "$node_major" =~ ^[0-9]+$ ]] || die "could not determine the Node.js version"
((node_major >= 22)) || die "Node.js 22.12 or newer is required"

"$python_path" - "$api_host" "$api_port" "$frontend_host" "$frontend_port" <<'PY'
import socket
import sys

for label, host, raw_port in (
    ("interface API", sys.argv[1], sys.argv[2]),
    ("frontend", sys.argv[3], sys.argv[4]),
):
    port = int(raw_port)
    with socket.socket() as candidate:
        candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            candidate.bind((host, port))
        except OSError as exc:
            raise SystemExit(f"Error: {label} port {host}:{port} is unavailable: {exc}")
PY

api_source="$(PYTHONPATH="$project_root/src" "$python_path" -c 'import geoagent_harness.interface_api.server as server; print(server.__file__)')"
status "project: $project_root"
status "interface API source: $api_source"
status "Node.js: $(node --version); Python: $($python_path --version 2>&1)"

probe_url() {
  local label="$1" url="$2"
  if command -v curl >/dev/null 2>&1 && curl --silent --fail --max-time 2 "$url" >/dev/null 2>&1; then
    status "$label: available"
  else
    status "$label: unavailable (optional; related actions will remain unavailable)"
  fi
}

probe_http_reachability() {
  local label="$1" url="$2" http_status
  if ! command -v curl >/dev/null 2>&1; then
    status "$label: not checked because curl is unavailable"
    return
  fi
  http_status="$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 2 "$url" 2>/dev/null || true)"
  if [[ "$http_status" =~ ^[1-5][0-9][0-9]$ ]]; then
    status "$label: reachable (HTTP $http_status; authentication is checked only by related actions)"
  else
    status "$label: unavailable (optional; related actions will remain unavailable)"
  fi
}

if [[ -n "${MODEL_NAME:-}" ]]; then
  status "model selection: configured (availability is checked by model actions)"
else
  status "model selection: missing; set MODEL_NAME in this launch terminal for model-assisted actions"
fi
ollama_base="${MODEL_BASE_URL:-http://127.0.0.1:11434/v1}"
probe_url "Ollama" "${ollama_base%/v1}/api/tags"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  status "Docker engine: available"
  for container_name in postgis geoserver; do
    if [[ "$(docker inspect --format '{{.State.Running}}' "$container_name" 2>/dev/null || true)" == "true" ]]; then
      status "$container_name container: running"
    else
      status "$container_name container: unavailable (optional; start it before related work)"
    fi
  done
else
  status "Docker engine: unavailable (optional; PostGIS and GeoServer actions will remain unavailable)"
fi

export INTERFACE_API_HOST="$api_host"
export INTERFACE_API_PORT="$api_port"
export INTERFACE_FRONTEND_ORIGIN="http://$frontend_host:$frontend_port"
export ENABLE_WRITE_TOOLS="$write_tools"
export ALLOW_OVERWRITE=false
export MODEL_BASE_URL="$ollama_base"
export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export GEOSERVER_BASE_URL="${GEOSERVER_BASE_URL:-http://127.0.0.1:8080/geoserver}"

if "$python_path" - "$POSTGRES_HOST" "$POSTGRES_PORT" <<'PY'
import socket
import sys

try:
    with socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=2):
        pass
except OSError:
    raise SystemExit(1)
PY
then
  status "PostGIS endpoint: reachable"
else
  status "PostGIS endpoint: unavailable (optional; load and database validation will remain unavailable)"
fi
probe_http_reachability "GeoServer" "$GEOSERVER_BASE_URL/rest/about/version.json"

if [[ "$write_tools" == "true" ]]; then
  status "execution authority: ENABLED for bounded, separately approved recipes"
else
  status "execution authority: DISABLED (default)"
fi
status "overwrite authority: DISABLED"

if [[ "$check_only" == "true" ]]; then
  status "startup checks passed; no service was started"
  exit 0
fi

cleanup() {
  local exit_code="${1:-0}"
  if [[ "$stopping" == "true" ]]; then
    return
  fi
  stopping=true
  trap - INT TERM EXIT
  for pid in "$frontend_pid" "$api_pid"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  for pid in "$frontend_pid" "$api_pid"; do
    if [[ -n "$pid" ]]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
  status "frontend and interface API stopped"
  exit "$exit_code"
}

trap 'cleanup 0' INT TERM
trap 'cleanup $?' EXIT

(
  cd "$project_root"
  exec bash scripts/serve_interface_dev.sh
) > >(sed -u 's/^/[api] /') 2> >(sed -u 's/^/[api:error] /' >&2) &
api_pid=$!

(
  cd "$project_root/interface"
  exec ./node_modules/.bin/vite --host "$frontend_host" --port "$frontend_port" --strictPort
) > >(sed -u 's/^/[frontend] /') 2> >(sed -u 's/^/[frontend:error] /' >&2) &
frontend_pid=$!

status "interface: http://$frontend_host:$frontend_port"
status "API health: http://$api_host:$api_port/api/v1/health"
status "press Ctrl+C once to stop both services"

set +e
wait -n "$api_pid" "$frontend_pid"
child_status=$?
set -e
if [[ "$stopping" != "true" ]]; then
  status "a service exited unexpectedly with status $child_status; stopping the other service"
  if [[ "$child_status" -eq 0 ]]; then
    child_status=1
  fi
  cleanup "$child_status"
fi
