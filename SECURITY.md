# Security Policy

## Supported versions

ActionCharter is currently an alpha prototype. Security fixes are applied to
the latest commit on `main`; older snapshots and generated demonstration
artifacts are not supported releases.

## MVP trust boundaries

- Model output is untrusted and must pass typed schema and policy checks.
- There is no unrestricted shell tool or unrestricted SQL tool.
- Input datasets are mounted read-only.
- Writes are limited to `data/output`, `traces`, and `reports`.
- Overwrite requires explicit approval; deletion is unavailable.
- Database secrets must not enter prompts, tool results, traces, or reports.
- Deterministic verification is the only success gate.
- Planner and critic have no database or GIS execution access.
- The shared model is reached through a configured local Ollama endpoint.

## Prototype limitations

Compose network settings do not constitute a complete egress firewall. The
prototype needs local access to host Ollama, and Docker/host firewall rules must
enforce any strict host-only egress policy. This repository is a research and
pilot implementation, not a hardened multi-user production control plane.

## Reporting

Report security problems privately through GitHub's **Report a vulnerability**
feature when it is enabled for the repository. Until then, contact the
maintainer through the private contact method listed on the GitHub profile.

Do not open a public issue containing credentials, private datasets, traces,
database details, exploit instructions or an unpatched vulnerability. Rotate
any credential accidentally committed to version control; removing it from the
latest commit is not sufficient.
