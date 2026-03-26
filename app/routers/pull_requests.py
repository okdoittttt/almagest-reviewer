"""Pull Request 조회 API."""
import httpx
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
    """PullRequest ORM 객체를 PullRequestListItem 스키마로 변환한다.

    Args:
        pr: PullRequest ORM 인스턴스.
        review_count: 연결된 리뷰 수.
        owner: 저장소 소유자 login.
        name: 저장소 이름.

    Returns:
        repo_owner, repo_name, review_count가 채워진 PullRequestListItem.
    """
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
    """특정 저장소의 PR 목록을 반환한다.

    Args:
        repo_id: 저장소 내부 PK.
        state: PR 상태 필터 (open/closed/merged).
        risk_level: 리스크 수준 필터 (LOW/MEDIUM/HIGH).
        session: 비동기 DB 세션.

    Returns:
        필터가 적용된 PullRequestListItem 목록 (최신순).

    Raises:
        HTTPException: repo_id에 해당하는 저장소가 없으면 404.
    """
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
    """전체 저장소의 PR 목록을 반환한다.

    Args:
        state: PR 상태 필터 (open/closed/merged).
        risk_level: 리스크 수준 필터 (LOW/MEDIUM/HIGH).
        review_decision: 최신 리뷰 판정 필터 (APPROVE/REQUEST_CHANGES/COMMENT).
        limit: 최대 반환 수 (기본 50, 최대 200).
        offset: 페이지네이션 오프셋.
        session: 비동기 DB 세션.

    Returns:
        필터가 적용된 PullRequestListItem 목록 (최신순).
    """
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
    """단일 PR의 상세 정보를 반환한다.

    Args:
        pr_id: PR 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        PullRequestDetail 스키마.

    Raises:
        HTTPException: pr_id에 해당하는 PR이 없으면 404.
    """
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
    """PR을 GitHub에서 병합하고 로컬 상태를 merged로 업데이트한다.

    Args:
        pr_id: PR 내부 PK.
        body: 병합 방식 (squash/rebase/merge).
        session: 비동기 DB 세션.

    Returns:
        병합 후 업데이트된 PullRequestDetail.

    Raises:
        HTTPException: PR이 없으면 404, 이미 닫혔거나 merge_method가 올바르지 않으면 422.
    """
    pr = await session.get(PullRequest, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    if pr.state != "open":
        raise HTTPException(status_code=422, detail="이미 닫힌 PR입니다")

    repo = await session.get(Repository, pr.repository_id)

    if body.merge_method not in ("squash", "rebase", "merge"):
        raise HTTPException(status_code=422, detail="merge_method는 squash, rebase, merge 중 하나여야 합니다")

    try:
        await github_client.merge_pull_request(
            installation_id=repo.installation_id,
            repo_owner=repo.owner,
            repo_name=repo.name,
            pull_number=pr.pr_number,
            merge_method=body.merge_method,
        )
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 403:
            gh_message = e.response.json().get("message", "") if e.response.content else ""
            if "not allowed" in gh_message.lower():
                raise HTTPException(
                    status_code=422,
                    detail=f"이 저장소에서는 해당 병합 방식이 허용되지 않습니다. "
                           f"저장소 설정(Settings → General → Merge button)에서 활성화해주세요. "
                           f"(GitHub: {gh_message})"
                )
            raise HTTPException(
                status_code=403,
                detail="GitHub App에 병합 권한이 없습니다. App 설정에서 Pull requests를 Read and write로 변경해주세요.",
            )
        if status == 405:
            raise HTTPException(status_code=422, detail="PR을 병합할 수 없습니다. 충돌 또는 병합 조건이 충족되지 않았습니다.")
        if status == 409:
            raise HTTPException(status_code=409, detail="병합 충돌이 발생했습니다.")
        raise HTTPException(status_code=502, detail=f"GitHub API 오류: {e.response.text}")

    pr.state = "merged"
    await session.flush()
    await session.refresh(pr)

    review_count = await session.scalar(
        select(func.count()).select_from(Review).where(Review.pull_request_id == pr_id)
    )
    return _to_list_item(pr, review_count or 0, repo.owner, repo.name)


@router.get("/pull-requests/{pr_id}/reviews", response_model=list[ReviewListItem])
async def list_pr_reviews(pr_id: int, session: AsyncSession = Depends(get_db)) -> list[ReviewListItem]:
    """특정 PR에 속한 리뷰 목록을 반환한다.

    Args:
        pr_id: PR 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        ReviewListItem 목록 (최신순).

    Raises:
        HTTPException: pr_id에 해당하는 PR이 없으면 404.
    """
    pr = await session.get(PullRequest, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    rows = await session.execute(
        select(Review).where(Review.pull_request_id == pr_id).order_by(Review.created_at.desc())
    )
    return [ReviewListItem.model_validate(r) for r in rows.scalars()]
