import pytest

from geoagent_harness.model.settings import (
    ModelSettingsError,
    load_model_settings,
)


def test_load_model_settings() -> None:
    settings = load_model_settings(
        {
            "MODEL_BASE_URL": "http://ollama:11434/v1/",
            "MODEL_NAME": "qwen-test",
            "MODEL_TIMEOUT_SECONDS": "90",
            "MODEL_MAX_TOKENS": "512",
        }
    )

    assert settings.base_url == "http://ollama:11434/v1"
    assert settings.model == "qwen-test"
    assert settings.timeout_seconds == 90
    assert settings.max_tokens == 512


def test_model_name_is_required() -> None:
    with pytest.raises(
        ModelSettingsError,
        match="MODEL_NAME",
    ):
        load_model_settings({})


def test_base_url_requires_v1() -> None:
    with pytest.raises(
        ModelSettingsError,
        match="/v1",
    ):
        load_model_settings(
            {
                "MODEL_BASE_URL": "http://ollama:11434",
                "MODEL_NAME": "qwen-test",
            }
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "file:///etc/passwd",
        "not-a-url",
        "",
    ],
)
def test_invalid_base_url_is_rejected(base_url: str) -> None:
    with pytest.raises(ModelSettingsError):
        load_model_settings(
            {
                "MODEL_BASE_URL": base_url,
                "MODEL_NAME": "qwen-test",
            }
        )


def test_timeout_has_upper_limit() -> None:
    with pytest.raises(
        ModelSettingsError,
        match="between",
    ):
        load_model_settings(
            {
                "MODEL_NAME": "qwen-test",
                "MODEL_TIMEOUT_SECONDS": "1000",
            }
        )
