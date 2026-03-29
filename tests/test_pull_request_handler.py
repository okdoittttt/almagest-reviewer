"""pull_request 웹훅 핸들러 단위 테스트."""
import pytest
from unittest.mock import AsyncMock, patch

from app.webhook.handlers.pull_request import handle_pull_request


def make_payload(action: str, draft: bool = False, head_sha: str = "abc1234") -> dict:
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
            "head": {"sha": head_sha},
        },
    }


@pytest.fixture
def mock_session():
    return AsyncMock()


# ── opened ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_opened_normal_pr_runs_pipeline(mock_pipeline, mock_session):
    """일반 PR opened → 파이프라인 실행."""
    await handle_pull_request("opened", make_payload("opened", draft=False), mock_session)
    mock_pipeline.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_opened_draft_pr_skips_pipeline(mock_pipeline, mock_session):
    """드래프트 PR opened → 파이프라인 실행 안 됨."""
    await handle_pull_request("opened", make_payload("opened", draft=True), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_synchronize_draft_pr_runs_pipeline(mock_pipeline, mock_session):
    """드래프트 상태에서 synchronize → 드래프트 가드 미적용, 파이프라인 실행."""
    await handle_pull_request("synchronize", make_payload("synchronize", draft=True), mock_session)
    mock_pipeline.assert_awaited_once()


# ── ready_for_review ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.review_exists_for_head_sha", new_callable=AsyncMock, return_value=False)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_ready_for_review_no_existing_review_runs_pipeline(mock_pipeline, mock_exists, mock_session):
    """ready_for_review + 기존 리뷰 없음 → 파이프라인 실행."""
    await handle_pull_request("ready_for_review", make_payload("ready_for_review"), mock_session)
    mock_pipeline.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.review_exists_for_head_sha", new_callable=AsyncMock, return_value=True)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_ready_for_review_existing_review_skips_pipeline(mock_pipeline, mock_exists, mock_session):
    """ready_for_review + 동일 head_sha 리뷰 이미 존재 → 파이프라인 스킵."""
    await handle_pull_request("ready_for_review", make_payload("ready_for_review"), mock_session)
    mock_pipeline.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhook.handlers.pull_request.review_exists_for_head_sha", new_callable=AsyncMock, return_value=False)
@patch("app.webhook.handlers.pull_request.run_full_review_pipeline", new_callable=AsyncMock)
async def test_ready_for_review_passes_correct_head_sha(mock_pipeline, mock_exists, mock_session):
    """ready_for_review → review_exists_for_head_sha에 올바른 head_sha 전달."""
    payload = make_payload("ready_for_review", head_sha="deadbeef1234")
    await handle_pull_request("ready_for_review", payload, mock_session)
    mock_exists.assert_awaited_once_with(mock_session, 111, 1, "deadbeef1234")
