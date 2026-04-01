"""Review / ReviewComment 응답 스키마."""
from datetime import datetime

from pydantic import BaseModel, computed_field


class ReviewListItem(BaseModel):
    id: int
    pull_request_id: int
    head_sha: str
    risk_level: str | None
    risk_score: float | None
    effective_risk_score: float | None
    effective_risk_level: str | None
    review_decision: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def display_risk_score(self) -> float | None:
        """effective_risk_score가 있으면 해당 값, 없으면 원본 risk_score를 반환한다."""
        return self.effective_risk_score if self.effective_risk_score is not None else self.risk_score

    @computed_field
    @property
    def display_risk_level(self) -> str | None:
        """effective_risk_level이 있으면 해당 값, 없으면 원본 risk_level을 반환한다."""
        return self.effective_risk_level if self.effective_risk_level is not None else self.risk_level


class ReviewDetail(ReviewListItem):
    pr_intent: dict | None
    risk_assessment: dict | None
    file_reviews: list
    final_review: str | None
    errors: list


class ReviewCommentOut(BaseModel):
    id: int
    review_id: int
    parent_id: int | None
    filename: str | None
    comment_type: str
    body: str | None
    severity: str | None
    is_addressed: bool
    addressed_at: datetime | None
    is_dismissed: bool
    dismissed_reason: str | None
    dismissed_by: str | None
    dismissed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
