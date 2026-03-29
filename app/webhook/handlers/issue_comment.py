"""issue_comment 웹훅 이벤트 핸들러."""
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.github import github_client
from app.services.review_service import get_most_recent_review

from ._helpers import run_full_review_pipeline

REVIEW_COOLDOWN_SECONDS = 60


async def handle_issue_comment(
    action: str,
    payload: dict,
    session: AsyncSession,
) -> None:
    """issue_comment 이벤트를 처리한다.

    Args:
        action: 웹훅 액션 (created, edited, deleted).
        payload: 웹훅 페이로드.
        session: 비동기 DB 세션.
    """
    if action != "created":
        return

    # PR 코멘트인지 확인 (이슈 코멘트와 구분)
    if "pull_request" not in payload["issue"]:
        return

    if payload["issue"]["state"] == "closed":
        return

    if "/re-review" not in payload["comment"]["body"].lower():
        return

    repo = payload["repository"]
    installation_id = str(payload["installation"]["id"])
    github_repo_id: int = repo["id"]
    repo_owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]
    pr_number: int = payload["issue"]["number"]

    # 쿨다운 체크
    recent_review = await get_most_recent_review(session, github_repo_id, pr_number)
    if recent_review is not None:
        elapsed = (datetime.now(timezone.utc) - recent_review.created_at).total_seconds()
        if elapsed < REVIEW_COOLDOWN_SECONDS:
            remaining = int(REVIEW_COOLDOWN_SECONDS - elapsed)
            logger.info(f"PR #{pr_number} 쿨다운 중, {remaining}초 남음")
            await github_client.create_pr_comment(
                installation_id=installation_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pull_number=pr_number,
                comment_body=f"리뷰 쿨다운 중입니다. {remaining}초 후에 다시 시도해주세요.",
            )
            return

    # 현재 head_sha 및 PR ID 조회
    pr_details = await github_client.get_pr_details(
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_number=pr_number,
    )
    github_pr_id: int = pr_details["id"]

    logger.info(f"PR #{pr_number} /re-review 커맨드로 리뷰 재실행")
    await run_full_review_pipeline(
        session=session,
        installation_id=installation_id,
        github_repo_id=github_repo_id,
        github_pr_id=github_pr_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=pr_number,
        trigger_source="re_review_command",
    )
