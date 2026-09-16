# Checkpoint 17M — loopback proposal compilation

Checkpoint 17M gives the guided interface its first live backend operation:
deterministic compilation of the exact `RecipeProposal` contract established by
17K and exercised by the 17L CLI parity fixture.

## Authority boundary

The service:

- binds only to `127.0.0.1` and rejects `0.0.0.0` or remote binding;
- accepts JSON bodies of at most 64 KiB;
- validates the complete proposal with the existing Pydantic contract;
- loads templates and skills only from its configured trusted project root;
- calls the existing Python compiler directly, never a shell or CLI subprocess;
- returns deterministic compilation and policy facts;
- asserts that save, approval and execution did not occur;
- rejects unknown endpoints and foreign browser origins;
- returns bounded redacted errors without local paths or exception details.

It exposes only:

| Method | Endpoint | Authority |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Report the non-writing boundary |
| `GET` | `/api/v1/recipe-templates` | Read the validated trusted catalog |
| `POST` | `/api/v1/recipe-proposals/compile` | Validate and compile in memory |

There are no generic filesystem, command, Python, SQL, network, MCP, save,
approval or execution endpoints.

## Local development

Run the API from the repository root in terminal one:

```bash
.venv/bin/geoagent serve-interface-api \
  --project-root . \
  --host 127.0.0.1 \
  --port 8765
```

Run Vite in terminal two:

```bash
corepack pnpm@10.17.1 --dir interface dev
```

Vite proxies the same-origin browser path `/api` to the loopback service. Open
the interface, choose **Templates**, fill the request and required inputs, and
select **Compile proposal**. A successful result displays the recipe identity,
ordered steps and counts of approval and validation gates, together with the
explicit statement that nothing was saved, approved or executed.

The static ignored template projection remains an offline fallback for browsing
templates. Compilation itself requires the local API.

## CLI parity check

Use the 17L fixture through both surfaces. The CLI command is:

```bash
.venv/bin/geoagent compile-recipe-proposal \
  examples/interface-parity/checkpoint17l-vector-conversion-proposal.json \
  --proposal-root examples/interface-parity \
  --project-root . \
  --pretty
```

For the interface, select `inspect_and_convert_vector` and provide the same
request, input and target path. Both results must resolve the ordered skills
`inspect_vector` then `convert_vector`, mark the recipe valid, require approval
and validation for `step_2`, and report no persistence, approval or execution.

## Deferred operations

Checkpoint 17M does not yet make the interface a complete CLI replacement.
Separate later slices must add visible, digest-bound controls for saving,
policy review, approval, execution progress, validation and evidence. The next
increment should add reviewed recipe persistence without combining it with
approval or execution.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py tests/test_interface_parity_fixture.py
corepack pnpm@10.17.1 --dir interface build
.venv/bin/pytest -q
git diff --check
```
