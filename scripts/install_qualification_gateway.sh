#!/usr/bin/env bash
# Optional M3c test environment; never installs into the application .venv.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
.venv/bin/python -c 'import sys,platform; assert sys.version_info[:2] == (3,12) and platform.system() == "Linux" and platform.machine() == "x86_64", "Gateway lock targets Linux x86_64 / Python 3.12"'
command -v uv >/dev/null
qualification_cache="$PWD/.local/qualification/download-cache"
qualification_python="$PWD/.local/qualification/venv/bin/python"
if [[ ! -x "$qualification_python" ]]; then
  uv venv .local/qualification/venv --python .venv/bin/python \
    --no-python-downloads --cache-dir "$qualification_cache"
fi
uv pip sync requirements/model-qualification.txt --python "$qualification_python" \
  --require-hashes --only-binary :all: --no-python-downloads --no-config \
  --default-index https://pypi.org/simple --cache-dir "$qualification_cache" --link-mode copy
"$qualification_python" -c 'from importlib.metadata import version; assert version("litellm") == "1.109.1"; print("Optional gateway environment ready: LiteLLM " + version("litellm"))'
