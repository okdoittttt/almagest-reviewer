"""ReviewComment ORM 모델."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ReviewComment(Base, TimestampMixin):
    """리뷰 내 개별 코멘트.

    Attributes:
        id: 내부 PK.
        review_id: 연결된 Review FK.
        parent_id: 답글 대상 코멘트 PK. 최상위 코멘트는 NULL.
        filename: 코멘트 대상 파일 경로.
        comment_type: 코멘트 유형 (issue/suggestion/reply).
        body: 코멘트 내용.
        is_addressed: 팔로업에서 처리 완료 여부.
        addressed_at: 처리 완료 시각.
    """

    __tablename__ = "review_comments"
    __table_args__ = (
        Index("ix_review_comments_review_id", "review_id"),
        Index("ix_review_comments_review_addressed", "review_id", "is_addressed"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("review_comments.id", ondelete="CASCADE"), nullable=True
    )
    filename: Mapped[str | None] = mapped_column(String(1000))
    comment_type: Mapped[str] = mapped_column(String(50), default="issue", nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_addressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    addressed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    review: Mapped["Review"] = relationship(  # noqa: F821
        "Review", back_populates="comments"
    )
    replies: Mapped[list["ReviewComment"]] = relationship(
        "ReviewComment",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="ReviewComment.parent_id",
    )
    parent: Mapped[Optional["ReviewComment"]] = relationship(
        "ReviewComment",
        back_populates="replies",
        remote_side="ReviewComment.id",
        foreign_keys="ReviewComment.parent_id",
    )
