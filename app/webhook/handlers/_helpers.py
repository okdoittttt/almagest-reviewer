"""웹훅 핸들러 공유 파이프라인 함수."""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.github import github_client, pr_collector
from app.reviewer import run_review
from app.services.review_service import persist_review_result


async def run_full_review_pipeline(
    session: AsyncSession,
    installation_id: str,
    github_repo_id: int,
    github_pr_id: int,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    trigger_source: str = "push",
) -> None:
    """PR 데이터 수집 → LangGraph 리뷰 → DB 저장 → GitHub 코멘트 게시 파이프라인.

    Args:
        session: 비동기 DB 세션.
        installation_id: GitHub App Installation ID.
        github_repo_id: GitHub 저장소 ID.
        github_pr_id: GitHub PR ID.
        repo_owner: 저장소 소유자 login.
        repo_name: 저장소 이름.
        pr_number: PR 번호.
        trigger_source: 리뷰 트리거 출처 (push, ready_for_review, re_review_command, label_removed).
    """
    logger.info(f"📋 PR 데이터 수집 시작: {repo_owner}/{repo_name} #{pr_number}")
    pr_data = await pr_collector.collect_pr_data(
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_number=pr_number,
        include_commits=True,
    )
    logger.info(
        f"📋 PR 데이터 수집 완료: {pr_data.changed_files_count}개 파일, "
        f"{pr_data.commits_count}개 커밋"
    )

    logger.info(f"🤖 AI 코드 리뷰 시작: PR #{pr_number}")
    review_result = await run_review(
        pr_data=pr_data,
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
    )
    logger.info(
        f"🤖 AI 코드 리뷰 완료: decision={review_result.get('review_decision')}, "
        f"errors={review_result.get('errors')}"
    )

    logger.info("💾 DB 저장 시작")
    await persist_review_result(
        session=session,
        installation_id=installation_id,
        github_repo_id=github_repo_id,
        github_pr_id=github_pr_id,
        pr_data=pr_data,
        review_result=review_result,
        trigger_source=trigger_source,
    )
    logger.info("💾 DB 저장 완료")

    final_review = review_result.get("final_review", "리뷰 생성 실패")
    review_decision = review_result.get("review_decision", "COMMENT")

    logger.info(f"💬 GitHub 코멘트 게시 시작: PR #{pr_number}")
    await github_client.create_pr_comment(
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_number=pr_number,
        comment_body=final_review,
    )

    logger.info(
        f"✅ PR #{pr_number} 리뷰 완료: {review_decision} - "
        f"{pr_data.changed_files_count} files, "
        f"{len(review_result.get('file_reviews', []))} reviews"
    )
