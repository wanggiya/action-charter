"""REAL-DATA TEST: full diabetes file -> preparation + statistics -> PostgreSQL -> verified reports.

What it does (no AI model calls; the plan is operator-authored):
  1. inspect_csv          readiness checks + statistics (describe by readmission, Pearson,
                          Spearman, OLS of time_in_hospital with HC3 errors)
  2. select_csv_columns   keep declared fields (streaming, all rows)
  3. decode_csv_codes     decode admission/discharge/source IDs with IDS_mapping.csv
  4. aggregate_csv        age x readmitted encounter counts and mean stay
  5. validate_postgres_import   read-only mapping preflight
  6. import_csv_to_postgres     NEW create-only table agent_sandbox.diabetes_full_<timestamp>
  7. export_postgres_to_csv     round-trip export
Then independently verifies counts, labels, group means, every round-trip value and a
direct SQL count, and writes reports to data/output/real_data_run_<timestamp>/.

Requirements:
  - data/input/test/diabetic_data.csv and data/input/test/IDS_mapping.csv
  - the app running (scripts/start_actioncharter.sh; API on 127.0.0.1:8765), because the
    running API owns the project write-policy lock. This script drives that API, switches
    "Allow writes" ON for the run and always switches it back OFF.
  - the reusable PostGIS container (.env + .secrets/postgis_password; schema agent_sandbox)

Run:  .venv/bin/python scripts/real_data_tests/diabetes_full_pipeline_live_api.py
Outputs under data/output/ contain patient-level rows and are git-ignored; delete when done.
First passing run: 2026-11-01, run e03ca8c9d48140db88bb45a6edda2653, 101,766 rows, 149.7 s.
"""
import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "scripts"), str(REPO / "src")]
os.chdir(REPO)

import psycopg  # noqa: E402
from diabetes_reference import CODES, read_book, reference, sha  # noqa: E402
from diabetes_test_flow import EXPORTED, SELECTED, make_plan  # noqa: E402
from postgres_workflow_acceptance import rejection  # noqa: E402

from geoagent_harness.approvals import plan_sha256  # noqa: E402
from geoagent_harness.interface_api import server as api  # noqa: E402
from geoagent_harness.interface_api.workflow import WorkflowRequest, authorize_workflow, prepare_workflow  # noqa: E402
from geoagent_harness.mcp_server.settings import MCPSettings  # noqa: E402
from geoagent_harness.postgres.service import inspect  # noqa: E402

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
TABLE = f"diabetes_full_{stamp}"
OUT = f"data/output/diabetes_full_{stamp}"
RESULTS = REPO / f"data/output/real_data_run_{stamp}"
SOURCE = "data/input/test/diabetic_data.csv"
CODEBOOK = "data/input/test/IDS_mapping.csv"
NUMERIC = ["time_in_hospital", "num_lab_procedures", "num_procedures", "num_medications",
           "number_outpatient", "number_emergency", "number_inpatient", "number_diagnoses"]

env = dict(l.split("=", 1) for l in (REPO / ".env").read_text().splitlines() if "=" in l and not l.lstrip().startswith("#"))
clean = lambda v: v.strip().strip("\"'")
DB = dict(host="127.0.0.1", port=int(clean(env.get("POSTGRES_PORT", "5432"))), dbname=clean(env["POSTGRES_DB"]), user=clean(env["POSTGRES_USER"]))
SECRET = REPO / ".secrets/postgis_password"


API = "http://127.0.0.1:8765/api/v1"


def call(path, payload=None):
    import urllib.request, urllib.error
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(API + path, data=data, method="GET" if payload is None else "POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{path} -> HTTP {e.code}: {e.read().decode()[:1500]}") from None


def set_writes(enabled):
    state = call("/write-policy")
    if state["enabled"] != enabled:
        state = call("/write-policy", {"enabled": enabled, "session_id": state["session_id"], "revision": state["revision"]})
    assert state["enabled"] == enabled, state
    return state


def execute(plan, root):
    plan_json = plan.model_dump(mode="json")
    stored = call("/plans/save-reviewed", {"action": "save_reviewed_plan", "planner_result": plan_json, "confirmed_plan_sha256": plan_sha256(plan.plan), "allowed_skill_ids": list(dict.fromkeys(s.skill for s in plan.plan.steps))})
    print("saved plan", stored["plan_filename"], flush=True)
    base = {"plan_filename": stored["plan_filename"], "confirmed_plan_sha256": stored["plan_sha256"]}
    set_writes(True)
    print("Allow writes: ON", flush=True)
    review = call("/workflow/prepare", {"action": "prepare_workflow", **base})
    try:
        call("/workflow/execute", {"action": "execute_workflow", **base, "confirmed_review_sha256": review["review_sha256"], "confirm_execution": True})
        raise AssertionError("execution without authorization was not rejected")
    except RuntimeError as e:
        print("unauthorized execute rejected as expected:", str(e)[:160], flush=True)
    approved = call("/workflow/authorize", {"action": "authorize_workflow", **base, "confirmed_review_sha256": review["review_sha256"], "approve_required_steps": True, "approver": "operator-requested-real-data-test", "reason": f"Operator-requested full-file test: new outputs {OUT}_* and new table agent_sandbox.{TABLE} only"})
    print("authorized", flush=True)
    workflow = {"action": "execute_workflow", **base, "confirmed_review_sha256": review["review_sha256"], "confirm_execution": True, "plan_approval_filename": approved["plan_approval_filename"], "recipe_approval_filename": approved["recipe_approval_filename"]}
    record = call("/workflow/runs", {"action": "start", "workflow": workflow})
    run_id = record["run_id"]; print("run started", run_id, flush=True)
    while record["status"] not in {"completed", "failed", "cancelled", "partial_failure", "interrupted"}:
        time.sleep(3)
        record = call("/workflow/runs", {"action": "read", "run_id": run_id})
    print("run status", record["status"], flush=True)
    assert record["status"] == "completed", json.dumps({k: record.get(k) for k in ("status", "finding", "error")}, default=str)[:2000]
    report = call("/workflow/runs", {"action": "report", "run_id": run_id})
    return {"step_results": record["steps"], "run_id": run_id, "plan_filename": stored["plan_filename"], "handoff": report["handoff"]}


def main():
    started = time.monotonic()
    expected = reference(REPO / SOURCE, REPO / CODEBOOK, REPO / SOURCE)
    book = read_book(REPO / CODEBOOK)
    settings = MCPSettings(project_root=REPO, input_root=REPO / "data/input", output_root=REPO / "data/output", postgres_host=DB["host"], postgres_port=DB["port"], postgres_database=DB["dbname"], postgres_user=DB["user"], postgres_password_file=SECRET, enable_write_tools=True)
    old = os.environ.copy()
    try:
        os.environ.update(ENABLE_WRITE_TOOLS="true", GEOAGENT_PROJECT_ROOT=str(REPO), POSTGRES_HOST=DB["host"], POSTGRES_PORT=str(DB["port"]), POSTGRES_DB=DB["dbname"], POSTGRES_USER=DB["user"], POSTGRES_PASSWORD_FILE=str(SECRET), ALLOWED_SCHEMAS="agent_sandbox")
        for key, suffix in {"INPUT": "data/input", "OUTPUT": "data/output", "TRACE": "traces", "REPORT": "reports", "PLAN": "plans", "APPROVAL": "approvals", "STATE": "workflow-state", "RECIPE": "workflow-recipes", "RECIPE_RUN": "recipe-runs", "RECIPE_EVIDENCE": "recipe-evidence", "SPATIAL_CONTRACT": "spatial-contracts"}.items():
            os.environ["GEOAGENT_" + key + "_ROOT"] = str(REPO / suffix)
        plan = make_plan(settings, sample=SOURCE, codebook=CODEBOOK, table=TABLE, output=OUT, streaming=True)
        plan.original_request = "Full-file readiness, statistics (descriptive by readmission, correlations, linear regression of length of stay), codebook decoding, age/readmission comparison and verified round trip into a new agent_sandbox table. No clinical exclusions or imputation."
        plan.plan.steps[0].arguments["analysis"]["statistics"] = {
            "question": "How do utilisation measures relate to length of stay, and how do they differ by readmission status?",
            "methods": ["describe", "pearson", "spearman", "linear_regression"],
            "columns": NUMERIC, "by": ["readmitted"], "missing_policy": "error",
            "regression": {"outcome": "time_in_hospital", "predictors": ["num_lab_procedures", "num_procedures", "num_medications", "number_diagnoses", "number_inpatient"], "covariance": "HC3"},
        }
        try:
            run = execute(plan, REPO)
        finally:
            set_writes(False); print("Allow writes: OFF", flush=True)
        out = {s["step_id"]: s for s in run["step_results"]}
        checks = {}
        analysis = out["step_1"]["outcome"]["table_analysis"]
        checks["inspected_rows_match"] = analysis["matched_row_count"] == expected["sample"]["rows"]
        checks["distinct_patients_match"] = analysis["distinct_counts"]["patient_nbr"] == expected["sample"]["distinct_patients"]
        stats = analysis.get("statistics") or {}
        checks["statistics_recorded"] = bool(stats)
        with (REPO / SOURCE).open(newline="", encoding="utf-8-sig") as f:
            original = list(csv.DictReader(f))
        with (REPO / f"{OUT}_decoded.csv").open(newline="") as f:
            decoded = list(csv.DictReader(f))
        checks["decoded_rows_and_labels_match"] = len(decoded) == len(original) and all(
            all(r[c] == s[c] for c in SELECTED) and all(r[c + "_label"] == book[c][s[c]] for c in CODES) for s, r in zip(original, decoded))
        with (REPO / f"{OUT}_groups.csv").open(newline="") as f:
            groups = list(csv.DictReader(f))
        counts = Counter((r["age"], r["readmitted"]) for r in original); sums = defaultdict(int)
        for r in original:
            sums[r["age"], r["readmitted"]] += int(r["time_in_hospital"])
        checks["group_counts_and_means_match"] = {(g["age"], g["readmitted"]): int(g["encounters"]) for g in groups} == counts and all(
            abs(Decimal(g["mean_stay"]) - Decimal(sums[g["age"], g["readmitted"]]) / counts[g["age"], g["readmitted"]]) < Decimal("1e-12") for g in groups)
        with (REPO / f"{OUT}_roundtrip.csv").open(newline="") as f:
            exported = list(csv.DictReader(f))
        wanted = Counter(tuple([("\\N" if c in {"race", "weight", "payer_code", "medical_specialty"} and r[c] == "?" else r[c]) for c in SELECTED] + [book[c][r[c]] for c in CODES] + ["false"]) for r in original)
        checks["roundtrip_every_value_matches"] = Counter(tuple(r[c] for c in EXPORTED) for r in exported) == wanted
        table = inspect("inspect_postgres_table", {"target_schema": "agent_sandbox", "target_table": TABLE}, settings)
        checks["db_rows_and_primary_key"] = table["row_count"] == len(original) and any(k["kind"] == "primary" and k["columns"] == ["encounter_id"] for k in table["key_constraints"])
        with psycopg.connect(**DB, password=SECRET.read_text().strip()) as db:
            count, patients = db.execute(f'SELECT count(*), count(DISTINCT patient_nbr) FROM agent_sandbox."{TABLE}"').fetchone()
        checks["independent_sql_count_matches"] = (count, patients) == (expected["sample"]["rows"], expected["sample"]["distinct_patients"])
        checks["source_files_unchanged"] = sha(REPO / SOURCE) == expected["source"]["sha256"] and sha(REPO / CODEBOOK) == expected["codebook"]["sha256"]

        RESULTS.mkdir(parents=True)
        docs = run["handoff"]
        (RESULTS / "analytical_report.md").write_text(docs["analytical_markdown"])
        (RESULTS / "technical_handoff.md").write_text(docs["technical_markdown"])
        (RESULTS / "statistics.json").write_text(json.dumps(stats, indent=2, default=str))
        summary = {"status": "passed" if all(checks.values()) else "FAILED", "checks": checks, "run_id": run["run_id"], "plan_filename": run["plan_filename"],
                   "table": f"agent_sandbox.{TABLE}", "outputs_prefix": OUT, "results_dir": str(RESULTS.relative_to(REPO)), "source_rows": len(original),
                   "distinct_patients": patients, "group_rows": len(groups), "operations": [s.skill for s in plan.plan.steps], "model_calls": 0,
                   "omitted_documents": docs.get("omitted_documents"), "elapsed_seconds": round(time.monotonic() - started, 1)}
        (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
    finally:
        os.environ.clear(); os.environ.update(old)


if __name__ == "__main__":
    main()
