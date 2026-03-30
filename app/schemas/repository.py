"""Repository 응답 스키마."""
from datetime import datetime

from pydantic import BaseModel


class RepositoryListItem(BaseModel):
    id: int
    github_repo_id: int
    owner: str
    name: str
    installation_id: str
    is_active: bool
    system_prompt: str | None = None
    pull_request_count: int = 0
    skill_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepositoryDetail(RepositoryListItem):
    pass


class RepositorySystemPromptUpdate(BaseModel):
    system_prompt: str | None
