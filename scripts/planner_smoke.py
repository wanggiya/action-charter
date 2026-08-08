"""Real smoke test for the non-executing Planner Agent."""

from __future__ import annotations

import json
from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.context_pack import (
    ContextPackError,
    build_context_pack,
)
from geoagent_harness.model import (
    ModelClientError,
    SharedModelClient,
    load_model_settings,
)
from geoagent_harness.model.settings import (
    ModelSettingsError,
)
from geoagent_harness.planner import (
    PlannerAgentError,
    run_planner_agent,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Call Ollama and validate its plan without executing it."""

    original_request = (
        "Inspect data/input/sample_points.geojson, "
        "load it into the agent_sandbox PostGIS schema as "
        "planner_smoke_points, deterministically validate the "
        "loaded layer, and generate a Markdown report. "
        "Create a plan only. Do not execute anything."
    )

    try:
        settings = load_model_settings()

        context_pack = build_context_pack(
            original_request,
            PROJECT_ROOT,
        )

        manifest = load_agent_manifest(
            "planner",
            PROJECT_ROOT / "agents",
        )

        client = SharedModelClient(settings)

        result = run_planner_agent(
            context_pack=context_pack,
            manifest=manifest,
            model_client=client,
        )
    except (
        ContextPackError,
        ModelClientError,
        ModelSettingsError,
        PlannerAgentError,
        OSError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "agent_id": result.agent_id,
                "model": result.model,
                "context_references": (
                    result.context_references
                ),
                "plan": result.plan.model_dump(
                    mode="json"
                ),
                "warnings": result.warnings,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())