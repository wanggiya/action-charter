# Capability expansion backlog

This note preserves the post-interface direction without granting new authority in Checkpoint 17A.

## Pandas / tabular-data capability

Pandas should be added as a governed backend capability, not installed on demand by the browser. A future checkpoint should add a pinned pandas dependency and named tabular operations with:

- explicit input and output schemas;
- allowlisted file formats and project-root paths;
- row, column, memory, and execution-time limits;
- deterministic validation and evidence output;
- version-pinned dependencies and reproducible container builds;
- the same plan, approval, execution, and verification boundaries used elsewhere.

Candidate first operations are inspect table, select/rename columns, filter rows with a bounded expression schema, join tables by declared keys, and export a reviewed result. Arbitrary Python expressions, dynamic imports, and UI-triggered package installation remain out of scope.

## Sockets and external services

Python's `socket` module is part of the standard library; installing it as a package is neither necessary nor the right extension mechanism. Raw socket access is network authority: it can bypass named tool contracts, host allowlists, request validation, and evidence capture.

Future connectivity should therefore use named backend adapters. Each adapter should declare protocol, allowed hosts, operations, credentials source, timeout, response limits, redaction rules, and evidence contract. The browser should call only an ActionCharter API; it should never receive secrets or arbitrary socket access.

## Proposed sequence

1. Complete the read-only workflow interface and its data contract.
2. Connect it to bounded run/evidence APIs without mutation.
3. Complete the end-to-end pilot and evidence story.
4. Add a governed capability registry and the first pandas adapter.
5. Add named external-service adapters only when a concrete workflow requires them.

This is backlog direction, not a claim that these capabilities already exist.
