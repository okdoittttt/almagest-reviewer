"""저장소 CRUD API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.skill import Skill
from app.schemas.repository import RepositoryListItem

router = APIRouter(prefix="/repositories", tags=["repositories"])


async def _list_repositories(session: AsyncSession) -> list[RepositoryListItem]:
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
    return await _list_repositories(session)


@router.patch("/{repo_id}/toggle", response_model=RepositoryListItem)
async def toggle_repository(repo_id: int, session: AsyncSession = Depends(get_db)) -> RepositoryListItem:
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
