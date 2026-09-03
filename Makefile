CRITIC_TASK_ID ?= checkpoint5e-points-20260809a
STATE_TASK_ID ?= checkpoint7c-state-check
SNAKEMAKE_EXPORT_DIR ?=
SKILL_CANDIDATE_DIR ?=
SKILL_TEST_RECORD_FILE ?=

.PHONY: checkpoint6-accept
.PHONY: critic-container
.PHONY: help install test inspect config build
.PHONY: agent-info mcp-smoke planner-smoke
.PHONY: state-container
.PHONY: workflow-version
.PHONY: snakemake-dry-run
.PHONY: skill-candidate-test
.PHONY: skill-candidate-test-record
.PHONY: builder-candidate-test
.PHONY: builder-candidate-test-record
.PHONY: checkpoint14f-readiness

help:
	@echo "make install     Install local development dependencies"
	@echo "make test        Run automated tests"
	@echo "make inspect     Inspect the public sample GeoJSON"
	@echo "make config      Validate interpolated Compose configuration"
	@echo "make build       Build agent and GIS images"
	@echo "make agent-info  Exercise all three independent agent images"
	@echo "make mcp-smoke   Run the read-only MCP protocol test"
	@echo "make planner-smoke Run the Planner Agent container"
	@echo "make critic-container  Run the read-only Critic container"
	@echo "make checkpoint6-accept Run complete Checkpoint 6 acceptance"
	@echo "make state-container Assess workflow state read-only"
	@echo "make workflow-version Show isolated Snakemake version"
	@echo "make snakemake-dry-run SNAKEMAKE_EXPORT_DIR=name Validate a replay DAG"
	@echo "make skill-candidate-test SKILL_CANDIDATE_DIR=<path>  Test one isolated generated skill candidate"
	@echo "make builder-candidate-test BUILDER_CANDIDATE_DIR=<path>  Test one isolated Builder candidate"
	@echo "make builder-candidate-test-record BUILDER_CANDIDATE_DIR=<path> BUILDER_TEST_RECORD_FILE=<path>  Save isolated Builder test evidence"
	@echo "make checkpoint14f-readiness Regenerate and assess the fixed pilot demo"

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

test:
	.venv/bin/pytest

inspect:
	.venv/bin/geoagent inspect-vector data/input/sample_points.geojson --pretty

checkpoint14f-readiness:
	.venv/bin/geoagent assess-pilot-demo-readiness \
		demonstrations/checkpoint14f/DEMO.json \
		--project-root . \
		--pretty

config:
	docker compose --profile agents --profile tools config --quiet

build:
	docker compose --profile agents --profile tools build

agent-info:
	docker compose --profile agents run --rm planner agent-info planner
	docker compose --profile agents run --rm executor
	docker compose --profile agents run --rm critic

mcp-smoke:
	.venv/bin/python scripts/mcp_smoke.py

planner-smoke:
	docker compose --profile agents run --rm planner

critic-container:
	docker compose --profile agents run --rm critic \
		critique-task \
		/workspace/traces/$(CRITIC_TASK_ID).json \
		/workspace/reports/$(CRITIC_TASK_ID).md \
		--trace-root /workspace/traces \
		--report-root /workspace/reports \
		--agents-root /app/agents \
		--pretty

checkpoint6-accept:
	.venv/bin/pytest
	docker compose --profile agents --profile tools config --quiet
	@sha256sum \
		traces/$(CRITIC_TASK_ID).json \
		reports/$(CRITIC_TASK_ID).md \
		> /tmp/geoagent-checkpoint6-before.sha256
	@docker compose --profile agents run --rm critic \
		critique-task \
		/workspace/traces/$(CRITIC_TASK_ID).json \
		/workspace/reports/$(CRITIC_TASK_ID).md \
		--trace-root /workspace/traces \
		--report-root /workspace/reports \
		--agents-root /app/agents \
		--pretty \
		> /tmp/geoagent-checkpoint6-critic.json
	@sha256sum \
		traces/$(CRITIC_TASK_ID).json \
		reports/$(CRITIC_TASK_ID).md \
		> /tmp/geoagent-checkpoint6-after.sha256
	@diff \
		/tmp/geoagent-checkpoint6-before.sha256 \
		/tmp/geoagent-checkpoint6-after.sha256
	@jq -e '.agent_id == "critic" and .deterministic_status == "validated_success" and .assessment.deterministic_status == "validated_success" and .assessment.conclusion == "supported" and .assessment.success_claimed == true and .assessment.edits_performed == false and .assessment.database_actions_performed == false and (.evidence_gaps | length) == 0' /tmp/geoagent-checkpoint6-critic.json

state-container:
	docker compose --profile agents run --rm executor \
			assess-workflow-resume \
			/workspace/workflow-state/$(STATE_TASK_ID).state.json \
			--state-root /workspace/workflow-state \
			--pretty

workflow-version:
	docker compose --profile workflow run --rm \
		workflow-runner \
		--version

snakemake-dry-run:
	@test -n "$(SNAKEMAKE_EXPORT_DIR)" || \
		(echo "SNAKEMAKE_EXPORT_DIR is required"; exit 2)
	@case "$(SNAKEMAKE_EXPORT_DIR)" in \
		*[!A-Za-z0-9._-]*|"") \
			echo "SNAKEMAKE_EXPORT_DIR must be a plain directory name"; \
			exit 2 ;; \
	esac
	docker compose --profile workflow run --rm \
		workflow-runner \
		--snakefile \
		"/workspace/snakemake-exports/$(SNAKEMAKE_EXPORT_DIR)/Snakefile" \
		--directory \
		"/workspace/snakemake-exports/$(SNAKEMAKE_EXPORT_DIR)" \
		--cores 1 \
		--dry-run

skill-candidate-test:
	@test -n "$(SKILL_CANDIDATE_DIR)" || \
		(echo "Error: SKILL_CANDIDATE_DIR is required"; exit 2)
	SKILL_CANDIDATE_DIR="$(abspath $(SKILL_CANDIDATE_DIR))" \
		docker compose \
		--profile skill-testing \
		run --rm skill-test-runner

skill-candidate-test-record:
	@test -n "$(SKILL_CANDIDATE_DIR)" || \
		(echo "Error: SKILL_CANDIDATE_DIR is required"; exit 2)
	@test -n "$(SKILL_TEST_RECORD_FILE)" || \
		(echo "Error: SKILL_TEST_RECORD_FILE is required"; exit 2)
	@mkdir -p "$(dir $(SKILL_TEST_RECORD_FILE))"
	@SKILL_CANDIDATE_DIR="$(abspath $(SKILL_CANDIDATE_DIR))" \
		docker compose \
		--profile skill-testing \
		run --rm skill-test-runner \
		> "$(SKILL_TEST_RECORD_FILE)"
	@echo "Candidate test record: $(SKILL_TEST_RECORD_FILE)"

builder-candidate-test:
	@test -n "$(BUILDER_CANDIDATE_DIR)" || \
		(echo "Error: BUILDER_CANDIDATE_DIR is required"; exit 2)
	SKILL_CANDIDATE_DIR="$(abspath $(BUILDER_CANDIDATE_DIR))" \
		docker compose \
		--profile skill-testing \
		run --rm skill-test-runner

builder-candidate-test-record:
	@test -n "$(BUILDER_CANDIDATE_DIR)" || \
		(echo "Error: BUILDER_CANDIDATE_DIR is required"; exit 2)
	@test -n "$(BUILDER_TEST_RECORD_FILE)" || \
		(echo "Error: BUILDER_TEST_RECORD_FILE is required"; exit 2)
	@mkdir -p "$(dir $(BUILDER_TEST_RECORD_FILE))"
	@SKILL_CANDIDATE_DIR="$(abspath $(BUILDER_CANDIDATE_DIR))" \
		docker compose \
		--profile skill-testing \
		run --rm skill-test-runner \
		> "$(BUILDER_TEST_RECORD_FILE)"
	@echo "Builder candidate test record: $(BUILDER_TEST_RECORD_FILE)"
