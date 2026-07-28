from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    load_settings,
    parse_flag,
)


@pytest.mark.parametrize(
    "value",
    [None, "", "false", "FALSE", "0", "no", "off"],
)
def test_false_and_missing_flags_stay_disabled(
    value: str | None,
) -> None:
    assert parse_flag(value, default=False) is False


@pytest.mark.parametrize(
    "value",
    ["true", "TRUE", "1", "yes", "on"],
)
def test_explicit_true_flags_are_enabled(value: str) -> None:
    assert parse_flag(value, default=False) is True


@pytest.mark.parametrize(
    "value",
    ["enabled", "tru", "perhaps", "2"],
)
def test_unknown_flag_values_fail_closed(value: str) -> None:
    assert parse_flag(value, default=False) is False


def test_settings_default_to_read_only() -> None:
    settings = load_settings({})

    assert settings.enable_write_tools is False
    assert settings.allow_overwrite is False
    assert settings.input_root == Path("data/input")
    assert settings.allowed_schemas == frozenset(
        {"agent_sandbox"}
    )


def test_invalid_allowed_schema_is_rejected() -> None:
    with pytest.raises(ValueError, match="schema"):
        load_settings(
            {
                "ALLOWED_SCHEMAS":
                    "agent_sandbox;drop_schema"
            }
        )