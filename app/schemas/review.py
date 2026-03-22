"""Review / ReviewComment 응답 스키마."""
from datetime import datetime

from pydantic import BaseModel


class ReviewListItem(BaseModel):
    id: int
    pull_request_id: int
    head_sha: str
    risk_level: str | None
    risk_score: float | None
    review_decision: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewDetail(ReviewListItem):
    pr_intent: dict | None
    risk_assessment: dict | None
    file_reviews: list
    final_review: str | None
    errors: list


class ReviewCommentOut(BaseModel):
    id: int
    review_id: int
    filename: str | None
    comment_type: str
    body: str | None
    is_addressed: bool
    addressed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
