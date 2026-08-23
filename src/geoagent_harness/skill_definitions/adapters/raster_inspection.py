"""Fixed renderer for raster-inspection candidates."""

from __future__ import annotations


class RasterInspectionRendererError(ValueError):
    """Raised when raster rendering is requested unsafely."""


def render_raster_inspection_candidate(
    *,
    skill_id: str,
) -> dict[str, str]:
    """Render the fixed inspect-raster candidate files."""

    if skill_id != "inspect_raster":
        raise RasterInspectionRendererError(
            "raster inspection adapter currently "
            "supports only inspect_raster"
        )

    package = (
        "src/geoagent_harness/skills/"
        "inspect_raster"
    )

    return {
        f"{package}/__init__.py": (
            '''"""Generated candidate for raster inspection."""

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
    InspectRasterResult,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)


__all__ = [
    "InspectRasterArguments",
    "InspectRasterResult",
    "inspect_raster",
]
'''
        ),
        f"{package}/schemas.py": (
            '''"""Typed schemas for raster inspection."""

from __future__ import annotations

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionResult,
)


class InspectRasterArguments(BaseModel):
    """Validated arguments for raster inspection."""

    model_config = ConfigDict(extra="forbid")

    path: Path
    input_root: Path


InspectRasterResult = RasterInspectionResult
'''
        ),
        f"{package}/policy.py": (
            '''"""Read-only policy for raster inspection."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionError,
    validate_raster_path,
)


class InspectRasterPolicyError(ValueError):
    """Raised when raster inspection policy fails."""


def validate_inspect_raster_request(
    *,
    path: Path,
    input_root: Path,
) -> Path:
    """Validate one raster request without modifying it."""

    try:
        return validate_raster_path(
            path,
            input_root=input_root,
        )
    except RasterInspectionError as exc:
        raise InspectRasterPolicyError(
            "raster inspection request failed policy"
        ) from exc
'''
        ),
        f"{package}/service.py": (
            '''"""Generated wrapper around the trusted raster adapter."""

from __future__ import annotations

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionResult,
    inspect_raster as execute_adapter,
)
from geoagent_harness.skills.inspect_raster.policy import (
    validate_inspect_raster_request,
)
from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)


def inspect_raster(
    arguments: InspectRasterArguments,
) -> RasterInspectionResult:
    """Inspect one approved raster without writing data."""

    safe_path = validate_inspect_raster_request(
        path=arguments.path,
        input_root=arguments.input_root,
    )

    return execute_adapter(
        safe_path,
        input_root=arguments.input_root,
    )
'''
        ),
        "tests/test_inspect_raster_schemas.py": (
            '''"""Generated schema contracts for inspect_raster."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)


def test_arguments_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        InspectRasterArguments(
            path=Path("sample.tif"),
            input_root=Path("input"),
            unexpected=True,
        )
'''
        ),
        "tests/test_inspect_raster_policy.py": (
            '''"""Generated policy contracts for inspect_raster."""

from pathlib import Path

import pytest

from geoagent_harness.skills.inspect_raster.policy import (
    InspectRasterPolicyError,
    validate_inspect_raster_request,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_policy_accepts_file_under_input_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )

    result = validate_inspect_raster_request(
        path=path,
        input_root=root,
    )

    assert result == path.resolve()


def test_policy_rejects_path_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    root.mkdir()

    outside = write_test_raster(
        tmp_path / "outside.tif"
    )

    with pytest.raises(
        InspectRasterPolicyError,
        match="failed policy",
    ):
        validate_inspect_raster_request(
            path=outside,
            input_root=root,
        )
'''
        ),
        "tests/test_inspect_raster_service.py": (
            '''"""Generated service contracts for inspect_raster."""

from pathlib import Path

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_inspects_fixture_without_modification(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )
    before = path.stat()

    result = inspect_raster(
        InspectRasterArguments(
            path=path,
            input_root=root,
        )
    )

    after = path.stat()

    assert result.status == "completed"
    assert result.driver == "GTiff"
    assert result.width == 3
    assert result.height == 2
    assert result.band_count == 1
    assert result.filesystem_modified is False
    assert result.database_modified is False

    assert before.st_size == after.st_size
    assert before.st_mtime_ns == after.st_mtime_ns
'''
        ),
        "tests/test_inspect_raster_contract.py": (
            '''"""Generated security contracts for inspect_raster."""

from pathlib import Path

import pytest

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)
from geoagent_harness.skills.inspect_raster.policy import (
    InspectRasterPolicyError,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    target = write_test_raster(
        root / "target.tif"
    )
    link = root / "link.tif"
    link.symlink_to(target)

    with pytest.raises(
        InspectRasterPolicyError,
        match="failed policy",
    ):
        inspect_raster(
            InspectRasterArguments(
                path=link,
                input_root=root,
            )
        )


def test_result_withholds_write_claims(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )

    result = inspect_raster(
        InspectRasterArguments(
            path=path,
            input_root=root,
        )
    )

    assert result.filesystem_modified is False
    assert result.database_modified is False
'''
        ),
    }

