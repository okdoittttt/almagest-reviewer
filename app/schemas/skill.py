"""Skill 응답/요청 스키마."""
from datetime import datetime

from pydantic import BaseModel


class SkillOut(BaseModel):
    id: int
    repository_id: int
    name: str
    description: str | None
    criteria: dict
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillCreate(BaseModel):
    name: str
    description: str | None = None
    criteria: dict = {}
    is_enabled: bool = True


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    criteria: dict | None = None
    is_enabled: bool | None = None
