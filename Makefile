CRITIC_TASK_ID ?= checkpoint5e-points-20260809a
STATE_TASK_ID ?= checkpoint7c-state-check

.PHONY: checkpoint6-accept
.PHONY: critic-container
.PHONY: help install test inspect config build
.PHONY: agent-info mcp-smoke planner-smoke
.PHONY: state-container

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

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

test:
	.venv/bin/pytest

inspect:
	.venv/bin/geoagent inspect-vector data/input/sample_points.geojson --pretty

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