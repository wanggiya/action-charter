from pathlib import Path
from geoagent_harness.intent.inventory import reviewed_context_inventory


def test_empty_inventory_is_read_only(tmp_path: Path):
    result = reviewed_context_inventory(project_root=tmp_path)
    assert result['reviews'] == [] and result['review_count'] == 0
    assert result['files_modified'] is result['model_called'] is result['execution_performed'] is False
    assert list(tmp_path.iterdir()) == []


def test_unsafe_directory_and_symlink_artifact_are_not_followed(tmp_path: Path):
    outside = tmp_path/'outside'
    outside.mkdir()
    (tmp_path/'reviewed-intents').symlink_to(outside, target_is_directory=True)
    contexts = tmp_path/'reviewed-contexts'
    contexts.mkdir()
    (contexts/f"context-review.{'a'*64}.json").symlink_to(outside/'missing')
    result = reviewed_context_inventory(project_root=tmp_path)
    assert result['findings'] == ['intent review directory is unavailable or unsafe']
    assert result['review_count'] == 1
    assert result['reviews'][0]['status'] == 'blocked'
    assert result['reviews'][0]['reviewed_at'] is None


def test_inventory_bounds_invalid_artifacts_without_parsing_them(tmp_path: Path):
    reviews = tmp_path/'reviewed-intents'
    reviews.mkdir()
    for index in range(55):
        (reviews/f'intent-review.{index:064x}.json').write_text('not json')
    result = reviewed_context_inventory(project_root=tmp_path)
    assert result['review_count'] == 50 and result['inventory_truncated'] is True
    assert all(item['status'] == 'blocked' for item in result['reviews'])
    assert result['approval_inferred'] is False
