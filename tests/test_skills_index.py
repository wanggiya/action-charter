"""Validate implemented skill metadata."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_INDEX = PROJECT_ROOT / "context" / "SKILLS_INDEX.yaml"


def test_implemented_skill_entrypoints_exist() -> None:
    payload: dict[str, Any] = yaml.safe_load(
        SKILLS_INDEX.read_text(encoding="utf-8")
    )

    implemented = [
        skill
        for skill in payload["skills"]
        if skill["status"] == "implemented"
    ]

    assert implemented

    for skill in implemented:
        entrypoint = skill.get("entrypoint")

        assert entrypoint, (
            f"implemented skill {skill['id']} "
            "has no entrypoint"
        )

        module_name, separator, attribute_name = (
            entrypoint.partition(":")
        )

        assert separator == ":", (
            f"invalid entrypoint for {skill['id']}"
        )
        assert module_name
        assert attribute_name

        module = importlib.import_module(module_name)

        assert hasattr(module, attribute_name), (
            f"{entrypoint} does not exist"
        )
        assert callable(getattr(module, attribute_name)), (
            f"{entrypoint} is not callable"
        )
