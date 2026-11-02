# Real-data tests

End-to-end tests on real (sensitive) datasets kept locally under `data/input/test/`.
The datasets and generated outputs are **not** in git (see `.gitignore`).

| Script | Data | What it proves | Needs |
|---|---|---|---|
| [diabetes_full_pipeline_live_api.py](diabetes_full_pipeline_live_api.py) | `diabetic_data.csv` (101,766 rows) + `IDS_mapping.csv` | Full governed pipeline through the running app: readiness, statistics (correlation, OLS), codebook decoding, grouping, create-only PostgreSQL import, round trip, analytical + technical reports, all independently verified | Running app (`scripts/start_actioncharter.sh`), reusable PostGIS container, `.secrets/postgis_password` |

Related, older acceptance scripts (disposable database, no running app needed):
`scripts/diabetes_workflow_acceptance.py` and its plan in `scripts/diabetes_test_flow.py`.

## Last results

| Date | Script | Result | Notes |
|---|---|---|---|
| 2026-11-01 | diabetes_full_pipeline_live_api.py | passed (9/9 checks, 149.7 s) | Table `agent_sandbox.diabetes_full_20261101_213702`; R² 0.267; report is statistician-level, not plain language; regression did not cluster by `patient_nbr` (71,518 patients / 101,766 encounters) |

Not yet covered: the AI agent planning this whole journey from one request, classification
(readmission prediction) and categorical tests.
