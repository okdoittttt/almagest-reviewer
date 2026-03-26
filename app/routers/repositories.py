"""저장소 CRUD API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.skill import Skill
from app.github import github_client
from app.schemas.repository import RepositoryListItem
from app.services.review_service import update_pr_state

router = APIRouter(prefix="/repositories", tags=["repositories"])


async def _list_repositories(session: AsyncSession) -> list[RepositoryListItem]:
    """모든 저장소를 PR/Skill 수와 함께 조회한다.

    Args:
        session: 비동기 DB 세션.

    Returns:
        pull_request_count, skill_count가 채워진 RepositoryListItem 목록 (최신순).
    """
    rows = await session.execute(
        select(
            Repository,
            func.count(PullRequest.id).label("pull_request_count"),
            func.count(Skill.id).label("skill_count"),
        )
        .outerjoin(PullRequest, PullRequest.repository_id == Repository.id)
        .outerjoin(Skill, Skill.repository_id == Repository.id)
        .group_by(Repository.id)
        .order_by(Repository.updated_at.desc())
    )
    result = []
    for repo, pr_count, skill_count in rows:
        item = RepositoryListItem.model_validate(repo)
        item.pull_request_count = pr_count
        item.skill_count = skill_count
        result.append(item)
    return result


@router.get("", response_model=list[RepositoryListItem])
async def list_repositories(session: AsyncSession = Depends(get_db)) -> list[RepositoryListItem]:
    """저장소 목록을 반환한다.

    Args:
        session: 비동기 DB 세션.

    Returns:
        RepositoryListItem 목록 (최신순).
    """
    return await _list_repositories(session)


@router.patch("/{repo_id}/toggle", response_model=RepositoryListItem)
async def toggle_repository(repo_id: int, session: AsyncSession = Depends(get_db)) -> RepositoryListItem:
    """저장소의 활성화 상태를 토글한다.

    Args:
        repo_id: 저장소 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        업데이트된 RepositoryListItem.

    Raises:
        HTTPException: repo_id에 해당하는 저장소가 없으면 404.
    """
    repo = await session.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    repo.is_active = not repo.is_active
    await session.flush()

    pr_count = await session.scalar(
        select(func.count()).select_from(PullRequest).where(PullRequest.repository_id == repo_id)
    )
    skill_count = await session.scalar(
        select(func.count()).select_from(Skill).where(Skill.repository_id == repo_id)
    )
    item = RepositoryListItem.model_validate(repo)
    item.pull_request_count = pr_count or 0
    item.skill_count = skill_count or 0
    return item


@router.post("/{repo_id}/sync-prs")
async def sync_pull_request_states(
    repo_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """GitHub에서 PR 상태를 가져와 DB와 동기화한다.

    DB에 open으로 저장된 PR 중 GitHub에서 실제로 closed/merged인 것들을 업데이트한다.

    Args:
        repo_id: 저장소 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        ``{"updated": N, "details": [{"pr_number": ..., "new_state": ...}, ...]}``

    Raises:
        HTTPException: repo_id에 해당하는 저장소가 없으면 404.
    """
    repo = await session.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    open_prs_result = await session.execute(
        select(PullRequest).where(
            PullRequest.repository_id == repo_id,
            PullRequest.state == "open",
        )
    )
    open_prs = open_prs_result.scalars().all()

    if not open_prs:
        return {"updated": 0, "details": []}

    gh_prs = await github_client.list_prs(
        installation_id=repo.installation_id,
        repo_owner=repo.owner,
        repo_name=repo.name,
        state="all",
    )
    gh_pr_map = {p["number"]: p for p in gh_prs}

    updated = []
    for pr in open_prs:
        gh_pr = gh_pr_map.get(pr.pr_number)
        if gh_pr is None:
            continue
        if gh_pr["state"] == "closed":
            new_state = "merged" if gh_pr.get("merged_at") else "closed"
            await update_pr_state(session, repo.github_repo_id, pr.pr_number, new_state)
            updated.append({"pr_number": pr.pr_number, "new_state": new_state})

    return {"updated": len(updated), "details": updated}
