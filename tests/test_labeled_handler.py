"""pull_request labeled/unlabeled 핸들러 단위 테스트."""
import pytest
from unittest.mock import AsyncMock, patch

from app.webhook.handlers.pull_request import handle_pull_request


def make_payload(action: str, label: str, draft: bool = False, current_labels: list[str] | None = None) -> dict:
    return {
        "action": action,
        "installation": {"id": 99},
        "repository": {
            "id": 111,
            "name": "test-repo",
            "owner": {"login": "test-user"},
        },
        "pull_request": {
            "id": 999,
            "number": 1,
            "draft": draft,
            "merged": False,
            "head": {"sha": "abc1234"},
            "labels": [{"name": l} for l in (current_labels or [])],
        },
        "label": {"name": label},
    }


def make_pr_details(draft: bool = False, labels: list[str] | None = None) -> dict:
    return {
        "id": 999,
        "draft": draft,
        "labels": [{"name": l} for l in (labels or [])],
    }


@pytest.fixture
def mock_session():
    return AsyncMock()


# ── labeled ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.create_pr_comment", new_callable=AsyncMock)
async def test_labeled_skip_label_posts_comment(mock_comment, mock_session):
    """스킵 라벨 추가 → GitHub 코멘트 게시."""
    await handle_pull_request("labeled", make_payload("labeled", "wip"), mock_session)
    mock_comment.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.create_pr_comment", new_callable=AsyncMock)
async def test_labeled_non_skip_label_no_comment(mock_comment, mock_session):
    """일반 라벨 추가 → 코멘트 없음."""
    await handle_pull_request("labeled", make_payload("labeled", "bug"), mock_session)
    mock_comment.assert_not_awaited()


# ── unlabeled ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.get_pr_details", new_callable=AsyncMock)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_unlabeled_skip_label_no_remaining_runs_pipeline(mock_pipeline, mock_details, mock_session):
    """스킵 라벨 제거 + 잔여 스킵 라벨 없음 + 비드래프트 → 파이프라인 실행."""
    mock_details.return_value = make_pr_details(draft=False, labels=["feature"])
    await handle_pull_request("unlabeled", make_payload("unlabeled", "wip"), mock_session)
    mock_pipeline.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.get_pr_details", new_callable=AsyncMock)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_unlabeled_skip_label_remaining_skip_label_skips(mock_pipeline, mock_details, mock_session):
    """스킵 라벨 제거 + 다른 스킵 라벨 여전히 존재 → 파이프라인 스킵."""
    mock_details.return_value = make_pr_details(draft=False, labels=["skip-review"])
    await handle_pull_request("unlabeled", make_payload("unlabeled", "wip"), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.get_pr_details", new_callable=AsyncMock)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_unlabeled_skip_label_draft_skips(mock_pipeline, mock_details, mock_session):
    """스킵 라벨 제거 + 드래프트 PR → 파이프라인 스킵."""
    mock_details.return_value = make_pr_details(draft=True, labels=[])
    await handle_pull_request("unlabeled", make_payload("unlabeled", "wip"), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.get_pr_details", new_callable=AsyncMock)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_unlabeled_non_skip_label_no_pipeline(mock_pipeline, mock_details, mock_session):
    """일반 라벨 제거 → get_pr_details 호출 없음, 파이프라인 스킵."""
    await handle_pull_request("unlabeled", make_payload("unlabeled", "bug"), mock_session)
    mock_details.assert_not_awaited()
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.github_client.get_pr_details", new_callable=AsyncMock)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_unlabeled_passes_label_removed_trigger_source(mock_pipeline, mock_details, mock_session):
    """스킵 라벨 제거 후 파이프라인 실행 시 trigger_source='label_removed' 전달."""
    mock_details.return_value = make_pr_details(draft=False, labels=[])
    await handle_pull_request("unlabeled", make_payload("unlabeled", "skip-review"), mock_session)
    _, kwargs = mock_pipeline.call_args
    assert kwargs["trigger_source"] == "label_removed"
