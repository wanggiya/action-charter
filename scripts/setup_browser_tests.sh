#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$project_root/interface/.playwright-browsers"
corepack pnpm@10.17.1 --dir "$project_root/interface" exec playwright install chromium
# Optional private audio runtime for minimal Debian/Ubuntu test environments.
# No system packages or browser profiles are changed.
shopt -s nullglob
browser_audio_libraries=("$project_root/interface/.browser-system-libs/runtime/usr/lib/"*/libasound.so.2)
if [[ "$(uname -s)" == "Linux" && ${#browser_audio_libraries[@]} -eq 0 ]] && ! ldconfig -p 2>/dev/null | rg 'libasound.so.2' >/dev/null; then
  if ! command -v apt-get >/dev/null || ! command -v dpkg-deb >/dev/null; then
    echo "Install Chromium's OS dependencies using your platform's package manager; audio runtime is missing."
    exit 2
  fi
  browser_lib_root="$project_root/interface/.browser-system-libs"
  mkdir -p "$browser_lib_root"
  browser_audio_package=libasound2t64
  if ! apt-cache show "$browser_audio_package" >/dev/null 2>&1; then
    browser_audio_package=libasound2
  fi
  (
    cd "$browser_lib_root"
    apt-get download "$browser_audio_package"
    for archive in "${browser_audio_package}"_*.deb; do
      [[ -f "$archive" ]] || continue
      [[ "$(dpkg-deb --field "$archive" Package)" == "$browser_audio_package" ]]
      dpkg-deb -x "$archive" runtime
    done
  )
fi
printf 'Browser tests use only: %s\n' "$PLAYWRIGHT_BROWSERS_PATH"
