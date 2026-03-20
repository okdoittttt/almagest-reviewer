"""SQLAlchemy DeclarativeBase 및 공통 Mixin 정의."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """모든 ORM 모델의 공통 베이스 클래스."""
    pass


class TimestampMixin:
    """created_at / updated_at 컬럼을 자동으로 추가하는 Mixin.

    Attributes:
        created_at: 레코드 생성 시각 (DB 서버 시간 기준, timezone-aware).
        updated_at: 레코드 마지막 수정 시각 (DB 서버 시간 기준, timezone-aware).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
