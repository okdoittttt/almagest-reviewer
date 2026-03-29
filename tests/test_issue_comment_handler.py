"""issue_comment 웹훅 핸들러 단위 테스트."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.webhook.handlers.issue_comment import handle_issue_comment, REVIEW_COOLDOWN_SECONDS


def make_payload(body: str = "/re-review", state: str = "open", is_pr: bool = True) -> dict:
    issue = {
        "number": 1,
        "state": state,
    }
    if is_pr:
        issue["pull_request"] = {"url": "https://api.github.com/repos/test/test/pulls/1"}

    return {
        "action": "created",
        "installation": {"id": 99},
        "repository": {
            "id": 111,
            "name": "test-repo",
            "owner": {"login": "test-user"},
        },
        "issue": issue,
        "comment": {"body": body},
    }


def make_review(created_seconds_ago: float):
    review = MagicMock()
    review.created_at = datetime.now(timezone.utc) - timedelta(seconds=created_seconds_ago)
    return review


@pytest.fixture
def mock_session():
    return AsyncMock()


# ── 필터링 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_non_created_action_skips(mock_pipeline, mock_session):
    """created 아닌 액션 → 스킵."""
    payload = make_payload()
    payload["action"] = "edited"
    await handle_issue_comment("edited", payload, mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_non_pr_comment_skips(mock_pipeline, mock_session):
    """PR 아닌 이슈 코멘트 → 스킵."""
    await handle_issue_comment("created", make_payload(is_pr=False), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_closed_pr_skips(mock_pipeline, mock_session):
    """닫힌 PR → 스킵."""
    await handle_issue_comment("created", make_payload(state="closed"), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_no_re_review_command_skips(mock_pipeline, mock_session):
    """/re-review 없는 코멘트 → 스킵."""
    await handle_issue_comment("created", make_payload(body="LGTM"), mock_session)
    mock_pipeline.assert_not_awaited()


# ── 쿨다운 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.github_client.create_pr_comment", new_callable=AsyncMock)
@patch("app.webhook.handlers.issue_comment.get_most_recent_review")
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_cooldown_active_posts_comment_and_skips(mock_pipeline, mock_recent, mock_comment, mock_session):
    """쿨다운 중 → 안내 코멘트 게시, 파이프라인 스킵."""
    mock_recent.return_value = AsyncMock(return_value=make_review(created_seconds_ago=10))
    mock_recent.return_value = make_review(created_seconds_ago=10)

    with patch("app.webhook.handlers.issue_comment.get_most_recent_review", new_callable=AsyncMock, return_value=make_review(10)):
        await handle_issue_comment("created", make_payload(), mock_session)

    mock_comment.assert_awaited_once()
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.github_client.get_pr_details", new_callable=AsyncMock, return_value={"id": 999})
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_cooldown_expired_runs_pipeline(mock_pipeline, mock_details, mock_session):
    """쿨다운 만료 → 파이프라인 실행."""
    old_review = make_review(created_seconds_ago=REVIEW_COOLDOWN_SECONDS + 1)
    with patch("app.webhook.handlers.issue_comment.get_most_recent_review", new_callable=AsyncMock, return_value=old_review):
        await handle_issue_comment("created", make_payload(), mock_session)

    mock_pipeline.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.github_client.get_pr_details", new_callable=AsyncMock, return_value={"id": 999})
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_no_prior_review_runs_pipeline(mock_pipeline, mock_details, mock_session):
    """이전 리뷰 없음 → 파이프라인 실행."""
    with patch("app.webhook.handlers.issue_comment.get_most_recent_review", new_callable=AsyncMock, return_value=None):
        await handle_issue_comment("created", make_payload(), mock_session)

    mock_pipeline.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.issue_comment.github_client.get_pr_details", new_callable=AsyncMock, return_value={"id": 999})
@patch("app.webhook.handlers.issue_comment.run_full_review_pipeline", new_callable=AsyncMock)
async def test_re_review_passes_correct_trigger_source(mock_pipeline, mock_details, mock_session):
    """파이프라인 실행 시 trigger_source='re_review_command' 전달."""
    with patch("app.webhook.handlers.issue_comment.get_most_recent_review", new_callable=AsyncMock, return_value=None):
        await handle_issue_comment("created", make_payload(), mock_session)

    _, kwargs = mock_pipeline.call_args
    assert kwargs["trigger_source"] == "re_review_command"
