# Contributing to ActionCharter

Thank you for considering a contribution. ActionCharter treats model output,
generated code and external data as untrusted until deterministic policy and
verification establish otherwise.

## Before opening a pull request

1. Open an issue for a substantial behavior, schema, trust-boundary or public
   API change.
2. Keep changes narrowly scoped and preserve existing compatibility surfaces.
3. Add deterministic tests for new behavior and failure paths.
4. Run the complete offline suite with `make test`.
5. Run `git diff --check` and verify that no generated evidence, credentials,
   private data or local configuration is staged.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
make test
```

The supported development environment is Linux. WSL2 with Docker Desktop is
the primary documented local configuration.

## Security and trust-boundary changes

Changes involving approvals, credentials, filesystem containment, execution,
MCP, PostGIS, evidence, release storage, Builder promotion or activation must:

- fail closed on missing or inconsistent evidence;
- keep model output non-authoritative;
- preserve exact identities and SHA-256 bindings;
- test path escapes, symlinks, unexpected entries and changed inputs where
  relevant;
- avoid expanding network, filesystem or credential authority implicitly.

Do not submit secrets, generated approvals, mutable outputs, operational
history, Critic records or release packages. Follow [SECURITY.md](SECURITY.md)
for vulnerabilities.

## Compatibility

ActionCharter `0.9.x` retains `geoagent_harness`, `geoagent`, `geoagent-mcp`,
existing evidence fields and established internal type names. Renaming those
interfaces requires a separately reviewed migration and compatibility plan.

By contributing, you agree that your contribution is licensed under the
Apache License, Version 2.0.
