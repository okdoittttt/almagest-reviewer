"""Skill CRUD API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.repository import Repository
from app.database.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillOut, SkillUpdate

router = APIRouter(tags=["skills"])


@router.get("/repositories/{repo_id}/skills", response_model=list[SkillOut])
async def list_skills(repo_id: int, session: AsyncSession = Depends(get_db)) -> list[SkillOut]:
    repo = await session.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    rows = await session.execute(
        select(Skill).where(Skill.repository_id == repo_id).order_by(Skill.name)
    )
    return [SkillOut.model_validate(s) for s in rows.scalars()]


@router.post("/repositories/{repo_id}/skills", response_model=SkillOut, status_code=201)
async def create_skill(
    repo_id: int, body: SkillCreate, session: AsyncSession = Depends(get_db)
) -> SkillOut:
    repo = await session.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    skill = Skill(
        repository_id=repo_id,
        name=body.name,
        description=body.description,
        criteria=body.criteria,
        is_enabled=body.is_enabled,
    )
    session.add(skill)
    await session.flush()
    await session.refresh(skill)
    return SkillOut.model_validate(skill)


@router.patch("/skills/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: int, body: SkillUpdate, session: AsyncSession = Depends(get_db)
) -> SkillOut:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    if body.name is not None:
        skill.name = body.name
    if body.description is not None:
        skill.description = body.description
    if body.criteria is not None:
        skill.criteria = body.criteria
    if body.is_enabled is not None:
        skill.is_enabled = body.is_enabled
    await session.flush()
    return SkillOut.model_validate(skill)


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(skill_id: int, session: AsyncSession = Depends(get_db)) -> None:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    await session.delete(skill)
