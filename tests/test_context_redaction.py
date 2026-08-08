from geoagent_harness.context_pack.redaction import (
    redact_text,
    redact_value,
)


def test_redacts_secret_assignment() -> None:
    result = redact_text(
        "password=hunter2 token:abc123 safe=value"
    )

    assert "hunter2" not in result
    assert "abc123" not in result
    assert "safe=value" in result


def test_redacts_credentials_in_url() -> None:
    result = redact_text(
        "postgresql://geoagent:private@postgis/geoagent"
    )

    assert "private" not in result
    assert "geoagent:private" not in result
    assert "[REDACTED]@" in result


def test_recursively_redacts_secret_keys() -> None:
    result = redact_value(
        {
            "name": "safe",
            "database_password": "private",
            "nested": {
                "api_key": "private-key",
            },
        }
    )

    assert result["name"] == "safe"
    assert result["database_password"] == "[REDACTED]"
    assert result["nested"]["api_key"] == "[REDACTED]"