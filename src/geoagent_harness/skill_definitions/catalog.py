"""Fixed catalog of trusted skill-generation adapters."""

from __future__ import annotations

from dataclasses import dataclass

from geoagent_harness.skill_definitions.schemas import (
    SkillProfile,
)


@dataclass(frozen=True)
class TrustedAdapter:
    """One adapter recognized by the generator."""

    adapter_id: str
    allowed_profiles: tuple[
        SkillProfile,
        ...
    ]
    fixture_required: bool
    entrypoint: str


_ADAPTERS: dict[str, TrustedAdapter] = {
    "raster_inspection": TrustedAdapter(
        adapter_id="raster_inspection",
        allowed_profiles=(
            SkillProfile.READ_ONLY_INSPECTION,
        ),
        fixture_required=True,
        entrypoint=(
            "geoagent_harness.skills.inspect_raster."
            "service:inspect_raster"
        ),
    ),
}


class TrustedAdapterError(ValueError):
    """Raised when an adapter is unknown or incompatible."""


def list_trusted_adapters(
) -> tuple[TrustedAdapter, ...]:
    """Return adapters in stable catalog order."""

    return tuple(_ADAPTERS.values())


def get_trusted_adapter(
    adapter_id: str,
) -> TrustedAdapter:
    """Return one trusted adapter or fail closed."""

    try:
        return _ADAPTERS[adapter_id]
    except KeyError as exc:
        raise TrustedAdapterError(
            f"unknown trusted adapter: "
            f"{adapter_id!r}"
        ) from exc

