"""PullRequest 응답 스키마."""
from datetime import datetime

from pydantic import BaseModel


class PullRequestListItem(BaseModel):
    id: int
    repository_id: int
    github_pr_id: int
    pr_number: int
    title: str | None
    author_login: str | None
    head_sha: str
    base_branch: str | None
    head_branch: str | None
    state: str
    risk_level: str | None
    triage_priority: int | None
    review_count: int = 0
    repo_owner: str = ""
    repo_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PullRequestDetail(PullRequestListItem):
    pass
