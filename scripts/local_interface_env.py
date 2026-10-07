#!/usr/bin/env python3
"""Load allowlisted host-launch settings as data; never source .env as shell."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shlex
import sys
from urllib.parse import urlsplit, urlunsplit

KEYS = frozenset({
    'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD_FILE',
    'MODEL_PROVIDER', 'MODEL_BASE_URL', 'MODEL_NAME', 'MODEL_TIMEOUT_SECONDS', 'MODEL_MAX_TOKENS',
    'ALLOWED_SCHEMAS', 'GEOSERVER_BASE_URL', 'GEOSERVER_USER', 'GEOSERVER_PASSWORD_FILE',
    'ALLOWED_GEOSERVER_WORKSPACES', 'ALLOWED_GEOSERVER_DATASTORES',
})
MARKER = 'ACTIONCHARTER_LOCAL_ENV_ROOT'


def read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 128_000:
        raise ValueError('Project .env must be a bounded regular file')
    result = {}
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        match = re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$', line)
        if not match or match[1] not in KEYS:
            continue
        try:
            values = shlex.split(match[2], comments=True, posix=True)
        except ValueError:
            raise ValueError(f'Invalid quoting in an allowlisted .env setting on line {number}') from None
        if len(values) > 1:
            raise ValueError(f'Quote spaces in the allowlisted .env setting on line {number}')
        result[match[1]] = values[0] if values else ''
    return result


def host_url(value: str, names: set[str]) -> str:
    parsed = urlsplit(value)
    if parsed.hostname not in names or parsed.username or parsed.password:
        return value
    netloc = '127.0.0.1' + (f':{parsed.port}' if parsed.port else '')
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def local_environment(root: Path, inherited: dict[str, str]) -> dict[str, str]:
    root = root.resolve()
    configured = read_dotenv(root / '.env')
    env = dict(inherited)
    for key, value in configured.items():
        env.setdefault(key, value)
    if 'POSTGRES_HOST' not in inherited and env.get('POSTGRES_HOST', 'postgis') == 'postgis':
        env['POSTGRES_HOST'] = '127.0.0.1'
    for key, names in [('MODEL_BASE_URL', {'host.docker.internal'}), ('GEOSERVER_BASE_URL', {'geoserver', 'host.docker.internal'})]:
        if key not in inherited and key in env:
            env[key] = host_url(env[key], names)
    for key, filename in [('POSTGRES_PASSWORD_FILE', 'postgis_password'), ('GEOSERVER_PASSWORD_FILE', 'geoserver_password')]:
        value = env.get(key)
        if key not in inherited and (not value or value == '/run/secrets/' + filename):
            value = str(root / '.secrets' / filename)
        if value:
            path = Path(value).expanduser()
            env[key] = str(path if path.is_absolute() else root / path)
    env[MARKER] = str(root)
    return env


def main():
    root = Path(sys.argv[1]).resolve()
    try:
        env = local_environment(root, dict(os.environ))
    except (OSError, ValueError):
        # Never print parsed values or exception messages containing .env data.
        raise SystemExit('Error: cannot load local .env settings; check file permissions and quoting') from None
    print('[startup] local configuration: .env non-secret settings loaded when present; terminal exports take precedence', flush=True)
    path = Path(env.get('POSTGRES_PASSWORD_FILE', ''))
    try:
        ready = False
        if path.is_file():
            with path.open('rb') as handle:
                ready = bool(handle.read(8192).strip())
    except OSError:
        ready = False
    print('[startup] PostGIS credential file: ' + ('readable and non-empty' if ready else 'missing, unreadable or empty; PostGIS execution will be blocked'), flush=True)
    os.execve('/bin/bash', ['bash', str(root / 'scripts/start_actioncharter.sh'), *sys.argv[2:]], env)


if __name__ == '__main__':
    main()
