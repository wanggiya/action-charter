"""Real connectivity test for the shared Ollama model."""

from __future__ import annotations

import json

from geoagent_harness.model import (
    ChatMessage,
    ModelClientError,
    ModelRequest,
    ModelSettingsError,
    SharedModelClient,
    load_model_settings,
)


def main() -> int:
    try:
        settings = load_model_settings()
        client = SharedModelClient(settings)

        result = client.complete(
            ModelRequest(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "Follow the user's output instruction exactly."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=(
                            "Reply with exactly GEOAGENT_OLLAMA_OK "
                            "and nothing else."
                        ),
                    ),
                ],
                temperature=0.0,
            )
        )
    except (ModelSettingsError, ModelClientError) as exc:
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

    passed = result.content.strip() == "GEOAGENT_OLLAMA_OK"

    print(
        json.dumps(
            {
                "status": "ok" if passed else "unexpected_response",
                "provider": result.provider,
                "model": result.model,
                "response": result.content,
            },
            indent=2,
        )
    )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
