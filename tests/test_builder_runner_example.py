from geoagent_harness.data.spatial.adapters import builder_runner_example


def test_builder_runner_fixture() -> None:
    assert builder_runner_example.VALUE == 42
