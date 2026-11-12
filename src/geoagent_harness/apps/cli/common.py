"""Shared CLI failure rendering; services retain policy and execution."""

from typing import Annotated, NoReturn
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.task_actions.command_actions import failures__failure_from_exception as failure_from_exception


def _raise_typed_failure(
    exception: BaseException,
    *,
    stage: FailureStage,
) -> NoReturn:
    """Render one redacted typed failure and exit."""

    failure = failure_from_exception(
        exception,
        stage=stage,
    )

    typer.echo(
        (
            f"Error [{failure.code}]: "
            f"{failure.message}"
        ),
        err=True,
    )

    raise typer.Exit(
        code=failure.exit_code
    ) from exception
