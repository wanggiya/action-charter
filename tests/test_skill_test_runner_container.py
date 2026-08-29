"""Static security tests for the skill-test container."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).parents[1]


def compose_service() -> dict:
    payload = yaml.safe_load(
        (
            PROJECT_ROOT / "compose.yaml"
        ).read_text(encoding="utf-8")
    )

    return payload["services"][
        "skill-test-runner"
    ]


def test_skill_runner_has_no_network() -> None:
    service = compose_service()

    assert service["network_mode"] == "none"
    assert "networks" not in service
    assert "extra_hosts" not in service


def test_skill_runner_is_read_only_and_non_privileged(
) -> None:
    service = compose_service()

    assert service["read_only"] is True
    assert "ALL" in service["cap_drop"]
    assert (
        "no-new-privileges:true"
        in service["security_opt"]
    )
    assert service["pids_limit"] == 128


def test_skill_runner_mounts_only_candidate_read_only(
) -> None:
    service = compose_service()

    volumes = service["volumes"]

    assert len(volumes) == 1
    assert volumes[0].endswith(
        ":/candidate:ro"
    )

    rendered = "\n".join(volumes)

    for prohibited in (
        "/workspace/approvals",
        "/workspace/data/output",
        "/workspace/plans",
        "/workspace/recipe-runs",
        "/workspace/recipe-evidence",
        "/run/secrets",
    ):
        assert prohibited not in rendered


def test_skill_runner_uses_fixed_pytest_image(
) -> None:
    service = compose_service()

    assert service["working_dir"] == "/candidate"
    assert service["build"]["dockerfile"] == (
        "docker/skill-test-runner/Dockerfile"
    )

    dockerfile = (
        PROJECT_ROOT
        / "docker"
        / "skill-test-runner"
        / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert (
        (
            'ENTRYPOINT ["python", '
            '"/app/run_candidate_tests.py"]'
        )
        in dockerfile
    )
    assert (
        "COPY docker/skill-test-runner/"
        "run_candidate_tests.py"
        in dockerfile
    )
    assert "USER geoagent" in dockerfile
    assert '".[gis]"' in dockerfile
    assert '".[mcp]"' not in dockerfile

def test_candidate_runner_extends_only_bounded_paths(
) -> None:
    runner_source = (
        PROJECT_ROOT
        / "docker"
        / "skill-test-runner"
        / "run_candidate_tests.py"
    ).read_text(encoding="utf-8")

    assert 'Path("/candidate")' in runner_source
    assert "geoagent_harness.__path__.insert" in (
        runner_source
    )
    assert (
        "skills_package.__path__.insert"
        in runner_source
    )
    assert "importlib.import_module" in runner_source

    assert "subprocess" not in runner_source
    assert "shell=True" not in runner_source
    assert "os.system" not in runner_source
    
    assert "candidate_tree_sha256" in (
        runner_source
    )
    assert "redirect_stdout" in runner_source
    assert "json.dumps" in runner_source
    assert "candidate_unchanged" in (
        runner_source
    )

def test_candidate_runner_supports_builder_manifest(
) -> None:
    runner_source = (
        PROJECT_ROOT
        / "docker"
        / "skill-test-runner"
        / "run_candidate_tests.py"
    ).read_text(encoding="utf-8")

    assert "BUILDER_CANDIDATE.json" in (
        runner_source
    )
    assert "BuilderCandidateManifest" in (
        runner_source
    )
    assert (
        '"builder_candidate_test"'
        in runner_source
    )
    assert (
        'candidate_type == "skill"'
        in runner_source
    )


def test_builder_mode_does_not_require_skills_package(
) -> None:
    runner_source = (
        PROJECT_ROOT
        / "docker"
        / "skill-test-runner"
        / "run_candidate_tests.py"
    ).read_text(encoding="utf-8")

    assert (
        "candidate must contain exactly one"
        in runner_source
    )
    assert "supported manifest" in runner_source
    assert (
        "candidate skills package is missing"
        in runner_source
    )

    conditional_position = runner_source.index(
        'if candidate_type == "skill":'
    )
    skills_import_position = runner_source.index(
        "skills_package = importlib.import_module"
    )

    assert (
        skills_import_position
        > conditional_position
    )
    assert "CANDIDATE_SKILL_ADAPTERS" in (
        runner_source
    )
    assert (
        '"geoagent_harness.skill_adapters"'
        in runner_source
    )
    assert (
        'candidate_type == "builder"'
        in runner_source
    )

