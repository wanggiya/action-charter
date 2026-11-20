# Reviewed agent know-how

These files guide reasoning. They are not the executable operations in `skills/`,
learned private memories, model training, tools or authorization. The same loader
serves chat planning (interface, CLI and MCP) and the standalone Planner. Exact
inspection fast paths retain their existing zero-model behavior.

Each `SKILL.md` begins with `---`, a JSON object, and another `---`, followed by
Markdown guidance. JSON is deliberately a strict subset of common front matter:
duplicate keys, YAML aliases and unknown properties are rejected.

Required header fields:

| Field | Contract |
|---|---|
| `id` | Lowercase hyphenated ID, matching its directory |
| `version` | Semantic version, such as `1.0.0` |
| `description` | One line, at most 180 characters |
| `when_to_use` | 1–16 literal applicability keywords, at most 64 characters each |
| `operations` | At most 12 existing registered operation IDs; empty for generic explanatory guidance |
| `data_classes` | Applicable context kinds from the existing model-data classification; **not permission to send data** |

Optional `family` and `specificity` (integer0–3, default0) select the most specific
applicable method within a family, avoiding duplicate generic/domain instructions.
They cannot expand the operation scope or confer domain truth.

The file limit is 4,096 bytes. Selection uses the request and bounded field-name
hints, requiring referenced operations to be available in the focused scope. Hints
establish relevance, not domain meaning or scientific suitability. At most three
files and 2,600 bytes of instruction payload are included. Whole files are omitted
when budgets are reached; instructions are not cut mid-method. Existing gateway,
schema, operation and authorization checks remain independent.

Only content-pinned built-in files are eligible. Project-local additions and edits
cannot enroll themselves. Missing, changed or unsafe assets are omitted with a
bounded reason. User-supplied guidance remains an untrusted proposal until source
review; no runtime installation or approval UI is added by this slice.

To add or revise a built-in file, review its method, applicability, supported
operations, limitations and examples. Increment its version and update its SHA-256
pin in `src/geoagent_harness/capabilities/agent_skills.py` as part of that source
review. Add meaningful selection/boundary cases in `tests/test_agent_knowhow.py` and
qualify the method on fixed synthetic tasks before making reliability claims.
Wheels include these same assets; the agent Docker build includes the directory.
No dependency or image installation is implied by editing an instruction.

Chat context records selected IDs, versions, digests, selection basis, payload bytes
and bounded omission reasons. The existing Context sent to Planner disclosure shows
the selected names. Standalone Planner proposals record selected provenance in
backend-generated warnings. Opening saved state never reloads instructions or calls
a model. A later send reselects the current reviewed version.
