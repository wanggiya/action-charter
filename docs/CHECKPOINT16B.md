# Checkpoint 16B — Governed GeoServer Layer Activation

Checkpoint 16B enables and advertises one existing GeoServer layer. It does
not create a workspace, datastore, feature type, layer or style. Planning,
approval and verification are non-writing. Execution accepts no arbitrary URL,
REST path, HTTP method or request body.

## Security boundary

Keep the existing GET rules from 16A. Before the approved execution only, grant
the dedicated role PUT access to exactly the authoritative feature-type resource.
Use the role name configured in your GeoServer; this development environment
uses `ROLE_ACTIONCHARTER`:

```properties
/rest/workspaces/geoagent_test/datastores/actioncharter_postgis/featuretypes/checkpoint3e_sample_points.json;PUT=ROLE_ACTIONCHARTER,ROLE_ADMINISTRATOR
```

Do not grant the role PUT access to `/rest/**`. Keep `ENABLE_WRITE_TOOLS=false`
except for the explicit execution command. Remove the exact PUT rule after the
approved operation when no further publication is planned.

## Plan

Run from WSL and store the plan beneath a controlled local directory:

```bash
mkdir -p geoserver-publication-evidence

GEOSERVER_BASE_URL=http://localhost:8080/geoserver \
  .venv/bin/geoagent plan-geoserver-publication \
  --plan-id publish-checkpoint3e \
  --workspace geoagent_test \
  --datastore actioncharter_postgis \
  --layer checkpoint3e_sample_points \
  --pretty > geoserver-publication-evidence/PLAN.json
```

Review the target, captured state and `plan_sha256` before approval.

## Approve

```bash
.venv/bin/geoagent record-geoserver-publication-approval \
  geoserver-publication-evidence/PLAN.json \
  --approver operator \
  --reason "Activate the exact reviewed demonstration layer." \
  --valid-for-minutes 30 \
  --pretty > geoserver-publication-evidence/APPROVAL.json
```

Review the approval and record its canonical digest with:

```bash
.venv/bin/python -c 'from pathlib import Path; from geoagent_harness.geoserver_publication import GeoServerPublicationApproval,publication_approval_sha256; value=GeoServerPublicationApproval.model_validate_json(Path("geoserver-publication-evidence/APPROVAL.json").read_text()); print(publication_approval_sha256(value))'
```

## Execute

Substitute the two reviewed digests. Use a one-command write-gate override so
it does not persist in the shell:

```bash
ENABLE_WRITE_TOOLS=true \
GEOSERVER_BASE_URL=http://localhost:8080/geoserver \
  .venv/bin/geoagent execute-geoserver-publication \
  geoserver-publication-evidence/PLAN.json \
  --approval-file geoserver-publication-evidence/APPROVAL.json \
  --confirm-plan-sha256 <plan-sha256> \
  --confirm-approval-sha256 <approval-sha256> \
  --pretty > geoserver-publication-evidence/EXECUTION.json
```

Success is withheld until fresh GETs confirm that the feature type and its
effective published-layer view are enabled and advertised. GeoServer persists
these flags on the feature-type resource; `layer.xml` does not contain them.
If validation fails after the fixed PUT, the executor restores the feature type
to the exact planned pre-state. It emits `rolled_back` when restoration is
confirmed, or `reconciliation_required` when restoration cannot be confirmed.
Both are non-success exit status 1, while preserving structured evidence.

## Independently verify

```bash
GEOSERVER_BASE_URL=http://localhost:8080/geoserver \
  .venv/bin/geoagent verify-geoserver-publication \
  geoserver-publication-evidence/EXECUTION.json \
  --plan-file geoserver-publication-evidence/PLAN.json \
  --pretty > geoserver-publication-evidence/VERIFICATION.json
```

The result must be `verified` with no findings. Keep this evidence directory
out of the commit unless a later demonstration checkpoint explicitly defines a
sanitized immutable evidence package.

## Live validation

The final prototype was exercised against GeoServer 2.28.0. The approved
feature-type PUT returned a `published` execution result, and a separate
read-only verification returned `verified` with no findings. Both observations
reported the feature type and effective published layer enabled and advertised.
Environment-specific plan, approval, execution, verification and server-log
files remain ignored local evidence and are not committed.
