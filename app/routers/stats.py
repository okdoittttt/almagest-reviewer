"""대시보드 통계 API."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.review import Review
from app.schemas.stats import StatsOut

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats(session: AsyncSession = Depends(get_db)) -> StatsOut:
    total_repos = await session.scalar(select(func.count()).select_from(Repository))
    active_repos = await session.scalar(
        select(func.count()).select_from(Repository).where(Repository.is_active == True)  # noqa: E712
    )
    total_prs = await session.scalar(select(func.count()).select_from(PullRequest))
    total_reviews = await session.scalar(select(func.count()).select_from(Review))
    approve_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.review_decision == "APPROVE")
    )
    rc_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.review_decision == "REQUEST_CHANGES")
    )
    comment_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.review_decision == "COMMENT")
    )
    avg_risk = await session.scalar(select(func.avg(Review.risk_score)).select_from(Review))

    return StatsOut(
        total_repositories=total_repos or 0,
        active_repositories=active_repos or 0,
        total_pull_requests=total_prs or 0,
        total_reviews=total_reviews or 0,
        approve_count=approve_count or 0,
        request_changes_count=rc_count or 0,
        comment_count=comment_count or 0,
        avg_risk_score=round(avg_risk, 3) if avg_risk is not None else None,
    )
