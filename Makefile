.PHONY: help install test inspect config build agent-info
.PHONY: help install test inspect config build agent-info mcp-smoke

help:
	@echo "make install     Install local development dependencies"
	@echo "make test        Run automated tests"
	@echo "make inspect     Inspect the public sample GeoJSON"
	@echo "make config      Validate interpolated Compose configuration"
	@echo "make build       Build agent and GIS images"
	@echo "make agent-info  Exercise all three independent agent images"
	@echo "make mcp-smoke   Run the read-only MCP protocol test"

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
	docker compose --profile agents run --rm planner
	docker compose --profile agents run --rm executor
	docker compose --profile agents run --rm critic

mcp-smoke:
	.venv/bin/python scripts/mcp_smoke.py