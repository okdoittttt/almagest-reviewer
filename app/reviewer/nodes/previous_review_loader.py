"""Previous Review Loader Node — 이전 리뷰 컨텍스트를 DB에서 로드합니다."""
from loguru import logger
from sqlalchemy import select

from app.database import async_session_factory
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.review import Review
from app.database.models.review_comment import ReviewComment
from app.reviewer.state import ReviewState


async def load_previous_review(state: ReviewState) -> dict:
    """이전 리뷰 결과를 DB에서 로드하는 노드.

    동일 PR의 가장 최근 Review를 조회하고, 미해결(is_addressed=False)
    ReviewComment를 파일별로 정리하여 ``previous_review`` 필드에 저장합니다.
    이전 리뷰가 없는 경우(첫 리뷰)에는 None으로 설정합니다.

    Args:
        state: 현재 리뷰 상태.

    Returns:
        ``previous_review`` 키를 포함하는 상태 업데이트 딕셔너리.
        previous_review 구조::

            {
                "review_id": int,
                "decision": str,            # APPROVE / REQUEST_CHANGES / COMMENT
                "risk_level": str,
                "final_review": str,
                "unresolved_by_file": {
                    "path/to/file.py": [
                        {"type": "issue", "body": "..."},
                        ...
                    ]
                },
                "unresolved_count": int,
            }
    """
    repo_owner = state["repo_owner"]
    repo_name = state["repo_name"]
    pr_number = state["pr_data"].pr_number

    try:
        async with async_session_factory() as session:
            # 저장소 조회
            repo_result = await session.execute(
                select(Repository).where(
                    Repository.owner == repo_owner,
                    Repository.name == repo_name,
                )
            )
            repo = repo_result.scalar_one_or_none()
            if repo is None:
                logger.info(f"🔍 저장소 미등록 — 이전 리뷰 없음 ({repo_owner}/{repo_name})")
                return {"previous_review": None}

            # PR 조회
            pr_result = await session.execute(
                select(PullRequest).where(
                    PullRequest.repository_id == repo.id,
                    PullRequest.pr_number == pr_number,
                )
            )
            pr = pr_result.scalar_one_or_none()
            if pr is None:
                logger.info(f"🔍 PR #{pr_number} 미등록 — 이전 리뷰 없음")
                return {"previous_review": None}

            # 가장 최근 리뷰 조회
            review_result = await session.execute(
                select(Review)
                .where(Review.pull_request_id == pr.id)
                .order_by(Review.created_at.desc())
                .limit(1)
            )
            review = review_result.scalar_one_or_none()
            if review is None:
                logger.info(f"🔍 PR #{pr_number} — 이전 리뷰 없음 (첫 리뷰)")
                return {"previous_review": None}

            # 미해결 코멘트 조회 (parent_id가 없는 원본 코멘트만)
            comments_result = await session.execute(
                select(ReviewComment).where(
                    ReviewComment.review_id == review.id,
                    ReviewComment.is_addressed.is_(False),
                    ReviewComment.parent_id.is_(None),
                )
            )
            unresolved = comments_result.scalars().all()

            # 파일별로 정리
            unresolved_by_file: dict[str, list[dict]] = {}
            for c in unresolved:
                key = c.filename or "_unknown"
                unresolved_by_file.setdefault(key, []).append(
                    {"id": c.id, "type": c.comment_type, "body": c.body}
                )

            previous_review = {
                "review_id": review.id,
                "decision": review.review_decision,
                "risk_level": review.risk_level,
                "final_review": review.final_review,
                "unresolved_by_file": unresolved_by_file,
                "unresolved_count": len(unresolved),
            }

            logger.info(
                f"📋 이전 리뷰 로드 완료: review_id={review.id}, "
                f"decision={review.review_decision}, "
                f"미해결 코멘트={len(unresolved)}개"
            )
            return {"previous_review": previous_review}

    except Exception as e:
        logger.warning(f"⚠️ 이전 리뷰 로드 실패 (리뷰는 계속 진행): {e}")
        return {"previous_review": None}
