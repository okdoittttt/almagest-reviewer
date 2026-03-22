"""대시보드 통계 스키마."""
from pydantic import BaseModel


class StatsOut(BaseModel):
    total_repositories: int
    active_repositories: int
    total_pull_requests: int
    total_reviews: int
    approve_count: int
    request_changes_count: int
    comment_count: int
    avg_risk_score: float | None
