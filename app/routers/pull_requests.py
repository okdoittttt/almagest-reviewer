"""Pull Request 조회 API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.review import Review
from app.github import github_client
from app.schemas.pull_request import PullRequestDetail, PullRequestListItem
from app.schemas.review import ReviewListItem

router = APIRouter(tags=["pull_requests"])


def _to_list_item(pr: PullRequest, review_count: int, owner: str, name: str) -> PullRequestListItem:
    item = PullRequestListItem.model_validate(pr)
    item.review_count = review_count
    item.repo_owner = owner
    item.repo_name = name
    return item


@router.get("/repositories/{repo_id}/pull-requests", response_model=list[PullRequestListItem])
async def list_pull_requests(
    repo_id: int,
    state: str | None = Query(None),
    risk_level: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
) -> list[PullRequestListItem]:
    repo = await session.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    q = (
        select(PullRequest, func.count(Review.id).label("review_count"))
        .outerjoin(Review, Review.pull_request_id == PullRequest.id)
        .where(PullRequest.repository_id == repo_id)
        .group_by(PullRequest.id)
        .order_by(PullRequest.updated_at.desc())
    )
    if state:
        q = q.where(PullRequest.state == state)
    if risk_level:
        q = q.where(PullRequest.risk_level == risk_level)

    rows = await session.execute(q)
    return [_to_list_item(pr, cnt, repo.owner, repo.name) for pr, cnt in rows]


@router.get("/pull-requests", response_model=list[PullRequestListItem])
async def list_all_pull_requests(
    state: str | None = Query(None),
    risk_level: str | None = Query(None),
    review_decision: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_db),
) -> list[PullRequestListItem]:
    q = (
        select(PullRequest, func.count(Review.id).label("review_count"), Repository.owner, Repository.name)
        .join(Repository, Repository.id == PullRequest.repository_id)
        .outerjoin(Review, Review.pull_request_id == PullRequest.id)
        .group_by(PullRequest.id, Repository.owner, Repository.name)
        .order_by(PullRequest.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if state:
        q = q.where(PullRequest.state == state)
    if risk_level:
        q = q.where(PullRequest.risk_level == risk_level)

    rows = await session.execute(q)
    result = []
    for pr, cnt, owner, name in rows:
        if review_decision:
            latest_review = await session.scalar(
                select(Review.review_decision)
                .where(Review.pull_request_id == pr.id)
                .order_by(Review.created_at.desc())
                .limit(1)
            )
            if latest_review != review_decision:
                continue
        result.append(_to_list_item(pr, cnt, owner, name))
    return result


@router.get("/pull-requests/{pr_id}", response_model=PullRequestDetail)
async def get_pull_request(pr_id: int, session: AsyncSession = Depends(get_db)) -> PullRequestDetail:
    pr = await session.get(PullRequest, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    repo = await session.get(Repository, pr.repository_id)
    review_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.pull_request_id == pr_id)
    )
    return _to_list_item(pr, review_count or 0, repo.owner, repo.name)


class MergeRequest(BaseModel):
    merge_method: str = "squash"


@router.post("/pull-requests/{pr_id}/merge", response_model=PullRequestDetail)
async def merge_pull_request(
    pr_id: int,
    body: MergeRequest,
    session: AsyncSession = Depends(get_db),
) -> PullRequestDetail:
    pr = await session.get(PullRequest, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    if pr.state != "open":
        raise HTTPException(status_code=422, detail="이미 닫힌 PR입니다")

    repo = await session.get(Repository, pr.repository_id)

    if body.merge_method not in ("squash", "rebase", "merge"):
        raise HTTPException(status_code=422, detail="merge_method는 squash, rebase, merge 중 하나여야 합니다")

    await github_client.merge_pull_request(
        installation_id=repo.installation_id,
        repo_owner=repo.owner,
        repo_name=repo.name,
        pull_number=pr.pr_number,
        merge_method=body.merge_method,
    )

    pr.state = "merged"
    await session.flush()

    review_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.pull_request_id == pr_id)
    )
    return _to_list_item(pr, review_count or 0, repo.owner, repo.name)


@router.get("/pull-requests/{pr_id}/reviews", response_model=list[ReviewListItem])
async def list_pr_reviews(pr_id: int, session: AsyncSession = Depends(get_db)) -> list[ReviewListItem]:
    pr = await session.get(PullRequest, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    rows = await session.execute(
        select(Review).where(Review.pull_request_id == pr_id).order_by(Review.created_at.desc())
    )
    return [ReviewListItem.model_validate(r) for r in rows.scalars()]
