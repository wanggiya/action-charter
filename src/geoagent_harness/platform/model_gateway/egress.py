"""Code-owned context classification and a fail-closed, content-free send decision."""
from __future__ import annotations

from hashlib import sha256
import json
from urllib.parse import urlsplit

from geoagent_harness.contracts.model_providers import (
    ContextPart, DataClass, DATA_CLASSES, EgressDecision,
)
from geoagent_harness.platform.model_gateway.schemas import ModelRequest
from geoagent_harness.platform.model_settings import ModelSettings


def components(request: ModelRequest):
    for index, message in enumerate(request.messages):
        yield 'message', index, message.content
    if request.response_schema is not None:
        yield 'response_schema', 0, json.dumps(
            request.response_schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def classify_request(request: ModelRequest, *, message_classes=None,
                     schema_class: DataClass = 'raw') -> ModelRequest:
    """Annotate exact assembled bytes; free text and schemas default to raw.

    This is an internal Python assembly API, never an HTTP/MCP/model input.
    Serialized context_class is retained for compatibility but cannot lower risk.
    """
    classes = tuple(message_classes) if message_classes is not None else ('raw',) * len(request.messages)
    if len(classes) != len(request.messages):
        raise ValueError('Each assembled message requires a classification')
    request._context_parts = tuple(ContextPart(
        kind=kind, index=index, data_class=classes[index] if kind == 'message' else schema_class,
        sha256=sha256(content.encode()).hexdigest(),
    ) for kind, index, content in components(request))
    return request


def highest_class(request: ModelRequest):
    tags = {(part.kind, part.index): part for part in request._context_parts}
    classes = []; unclassified = 0
    for kind, index, content in components(request):
        part = tags.get((kind, index))
        if part is None or part.sha256 != sha256(content.encode()).hexdigest():
            classes.append('raw'); unclassified += 1
        else:
            classes.append(part.data_class)
    return max(classes, key=DATA_CLASSES.index, default='raw'), unclassified


def allowance(settings: ModelSettings):
    from geoagent_harness.platform.model_gateway.profiles import loopback
    configured = settings.data_allowed if settings.data_allowed in DATA_CLASSES else 'none'
    # Preserve the existing implicit Docker-to-host runtime bridge. A local relay
    # remains operator-trusted configuration, not proof of its downstream isolation.
    bridge = settings.provider_profile_id == 'local' and urlsplit(settings.base_url).hostname == 'host.docker.internal'
    restricted = not loopback(settings.base_url) and not bridge
    return configured, 'none' if restricted else configured, restricted


def evaluate(request: ModelRequest, settings: ModelSettings) -> EgressDecision:
    highest, unknown = highest_class(request)
    configured, effective, restricted = allowance(settings)
    return EgressDecision(highest_class=highest, data_allowed=effective,
        configured_data_allowed=configured, allowed=DATA_CLASSES.index(highest) <= DATA_CLASSES.index(effective),
        unclassified_parts=unknown, nonlocal_restricted=restricted)
