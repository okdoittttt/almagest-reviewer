"""Review ORM 모델."""
from datetime import datetime

from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """PR 리뷰 결과 스냅샷.

    Attributes:
        id: 내부 PK.
        pull_request_id: 연결된 PullRequest FK.
        head_sha: 리뷰가 수행된 커밋 SHA.
        risk_level: 리스크 수준 (LOW/MEDIUM/HIGH).
        risk_score: 리스크 점수 (0.0 ~ 1.0).
        pr_intent: PR 의도 분석 결과 (JSONB).
        risk_assessment: 리스크 평가 결과 (JSONB).
        file_reviews: 파일별 리뷰 목록 (JSONB array).
        final_review: 최종 리뷰 텍스트.
        review_decision: 리뷰 결정 (APPROVE/REQUEST_CHANGES/COMMENT).
        retry_count: 재시도 횟수.
        errors: 처리 중 발생한 에러 목록 (JSONB array).
    """

    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_pull_request_created", "pull_request_id", "created_at"),
        Index("ix_reviews_head_sha", "head_sha"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pull_request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    risk_score: Mapped[float | None] = mapped_column(Float)
    pr_intent: Mapped[dict | None] = mapped_column(JSONB)
    risk_assessment: Mapped[dict | None] = mapped_column(JSONB)
    file_reviews: Mapped[list] = mapped_column(JSONB, default=list, nullable=False, server_default="[]")
    final_review: Mapped[str | None] = mapped_column(Text)
    review_decision: Mapped[str | None] = mapped_column(String(50))
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[list] = mapped_column(JSONB, default=list, nullable=False, server_default="[]")

    pull_request: Mapped["PullRequest"] = relationship(  # noqa: F821
        "PullRequest", back_populates="reviews"
    )
    comments: Mapped[list["ReviewComment"]] = relationship(  # noqa: F821
        "ReviewComment", back_populates="review", cascade="all, delete-orphan"
    )
