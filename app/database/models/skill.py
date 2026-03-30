"""Skill ORM 모델."""
from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    """저장소별 리뷰 스킬 설정.

    Attributes:
        id: 내부 PK.
        repository_id: 연결된 Repository FK.
        name: 스킬 이름.
        description: 스킬 설명.
        criteria: 스킬 적용 기준 (자유형식 텍스트).
        file_patterns: 이 스킬을 적용할 파일 경로 패턴 목록 (glob). 빈 배열이면 모든 파일에 적용.
        is_enabled: 활성 여부.
    """

    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("repository_id", "name", name="uq_skills_repository_name"),
        Index("ix_skills_repository_enabled", "repository_id", "is_enabled"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_patterns: Mapped[list] = mapped_column(JSONB, default=list, nullable=False, server_default="[]")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="skills"
    )
