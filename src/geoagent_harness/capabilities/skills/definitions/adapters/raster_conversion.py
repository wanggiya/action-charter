"""Fixed renderer for raster-conversion candidates."""

from __future__ import annotations


class RasterConversionRendererError(ValueError):
    """Raised when raster conversion cannot be rendered."""


def render_raster_conversion_candidate(
    *,
    skill_id: str,
) -> dict[str, str]:
    """Render fixed convert-raster candidate files."""

    if skill_id != "convert_raster":
        raise RasterConversionRendererError(
            "raster conversion adapter currently "
            "supports only convert_raster"
        )

    package = (
        "src/geoagent_harness/skills/"
        "convert_raster"
    )

    return {
        f"{package}/__init__.py": (
            '''"""Generated candidate for controlled raster conversion."""

from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
    ConvertRasterResult,
    ConvertRasterValidationResult,
    RasterResampling,
)
from geoagent_harness.skills.convert_raster.service import (
    convert_raster,
)
from geoagent_harness.skills.convert_raster.validation import (
    validate_raster_conversion,
)


__all__ = [
    "ConvertRasterArguments",
    "ConvertRasterResult",
    "ConvertRasterValidationResult",
    "RasterResampling",
    "convert_raster",
    "validate_raster_conversion",
]
'''
        ),
        f"{package}/schemas.py": (
            '''"""Typed schemas for controlled raster conversion."""

from __future__ import annotations

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
)

from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionResult,
    RasterConversionValidationResult,
    RasterResampling,
)


class ConvertRasterArguments(BaseModel):
    """Validated arguments for raster conversion."""

    model_config = ConfigDict(extra="forbid")

    path: Path
    target_path: Path
    target_crs: str
    resampling: RasterResampling = (
        RasterResampling.NEAREST
    )


ConvertRasterResult = RasterConversionResult
ConvertRasterValidationResult = (
    RasterConversionValidationResult
)
'''
        ),
        f"{package}/policy.py": (
            '''"""Deterministic policy for raster conversion."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionPlan,
    plan_raster_conversion,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterPolicyError(ValueError):
    """Raised when raster conversion policy fails."""


def validate_convert_raster_request(
    *,
    arguments: ConvertRasterArguments,
    settings: MCPSettings,
) -> RasterConversionPlan:
    """Build a non-executing conversion plan."""

    try:
        return plan_raster_conversion(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            input_root=settings.input_root,
            output_root=settings.output_root,
            resampling=arguments.resampling,
        )
    except RasterConversionError as exc:
        raise ConvertRasterPolicyError(
            "raster conversion request failed policy"
        ) from exc
'''
        ),
        f"{package}/service.py": (
            '''"""Generated wrapper around the trusted raster adapter."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionResult,
    convert_raster as execute_adapter,
)
from geoagent_harness.skills.convert_raster.policy import (
    ConvertRasterPolicyError,
    validate_convert_raster_request,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterError(RuntimeError):
    """Raised when controlled raster conversion fails."""


def convert_raster(
    arguments: ConvertRasterArguments,
    *,
    settings: MCPSettings,
) -> RasterConversionResult:
    """Create one approved output pending validation."""

    try:
        validate_convert_raster_request(
            arguments=arguments,
            settings=settings,
        )

        return execute_adapter(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            settings=settings,
            resampling=arguments.resampling,
        )
    except (
        ConvertRasterPolicyError,
        RasterConversionError,
    ) as exc:
        raise ConvertRasterError(
            "controlled raster conversion failed"
        ) from exc
'''
        ),
        f"{package}/validation.py": (
            '''"""Independent validation for raster conversion."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionValidationResult,
    validate_raster_conversion as execute_validation,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterValidationError(ValueError):
    """Raised when raster validation cannot complete."""


def validate_raster_conversion(
    arguments: ConvertRasterArguments,
    *,
    settings: MCPSettings,
) -> RasterConversionValidationResult:
    """Validate one exact source and target pair."""

    try:
        return execute_validation(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            input_root=settings.input_root,
            output_root=settings.output_root,
        )
    except RasterConversionError as exc:
        raise ConvertRasterValidationError(
            "raster conversion validation failed"
        ) from exc
'''
        ),
        "tests/test_convert_raster_schemas.py": (
            '''"""Generated schema contracts for convert_raster."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
    RasterResampling,
)


def test_arguments_are_strict() -> None:
    with pytest.raises(ValidationError):
        ConvertRasterArguments(
            path=Path("input/sample.tif"),
            target_path=Path("output/result.tif"),
            target_crs="EPSG:3857",
            unexpected=True,
        )


def test_resampling_is_allowlisted() -> None:
    arguments = ConvertRasterArguments(
        path=Path("input/sample.tif"),
        target_path=Path("output/result.tif"),
        target_crs="EPSG:3857",
        resampling="bilinear",
    )

    assert (
        arguments.resampling
        == RasterResampling.BILINEAR
    )

    with pytest.raises(ValidationError):
        ConvertRasterArguments(
            path=Path("input/sample.tif"),
            target_path=Path("output/result.tif"),
            target_crs="EPSG:3857",
            resampling="arbitrary",
        )
'''
        ),
        "tests/test_convert_raster_policy.py": (
            '''"""Generated policy contracts for convert_raster."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_raster.policy import (
    ConvertRasterPolicyError,
    validate_convert_raster_request,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_policy_plans_without_writing(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    plan = validate_convert_raster_request(
        arguments=ConvertRasterArguments(
            path=source,
            target_path=target,
            target_crs="EPSG:3857",
        ),
        settings=MCPSettings(
            input_root=input_root,
            output_root=output_root,
        ),
    )

    assert plan.execution_allowed is False
    assert plan.approval_required is True
    assert plan.validation_required is True
    assert not target.exists()


def test_policy_rejects_output_escape(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        ConvertRasterPolicyError,
        match="failed policy",
    ):
        validate_convert_raster_request(
            arguments=ConvertRasterArguments(
                path=source,
                target_path=(
                    tmp_path / "outside.tif"
                ),
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
            ),
        )
'''
        ),
        "tests/test_convert_raster_service.py": (
            '''"""Generated service contracts for convert_raster."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.skills.convert_raster.service import (
    ConvertRasterError,
    convert_raster,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_service_requires_write_authority(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        ConvertRasterError,
        match="controlled raster conversion failed",
    ):
        convert_raster(
            ConvertRasterArguments(
                path=source,
                target_path=(
                    output_root / "result.tif"
                ),
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
                enable_write_tools=False,
            ),
        )
'''
        ),
        "tests/test_convert_raster_contract.py": (
            '''"""Generated security contracts for convert_raster."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.skills.convert_raster.service import (
    ConvertRasterError,
    convert_raster,
)
from geoagent_harness.skills.convert_raster.validation import (
    validate_raster_conversion,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_conversion_withholds_success_until_validation(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    arguments = ConvertRasterArguments(
        path=source,
        target_path=target,
        target_crs="EPSG:3857",
    )
    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=True,
    )

    result = convert_raster(
        arguments,
        settings=settings,
    )

    assert result.validation_performed is False
    assert result.final_success_claimed is False

    validation = validate_raster_conversion(
        arguments,
        settings=settings,
    )

    assert validation.passed is True
    assert validation.validation_performed is True
    assert validation.final_success_claimed is True


def test_existing_output_is_not_overwritten(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = write_test_raster(
        output_root / "result.tif"
    )
    before = target.read_bytes()

    with pytest.raises(ConvertRasterError):
        convert_raster(
            ConvertRasterArguments(
                path=source,
                target_path=target,
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
                enable_write_tools=True,
            ),
        )

    assert target.read_bytes() == before
'''
        ),
    }

