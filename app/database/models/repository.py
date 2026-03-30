"""Repository ORM 모델."""
from sqlalchemy import BigInteger, Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    """GitHub 저장소 정보.

    Attributes:
        id: 내부 PK.
        github_repo_id: GitHub에서 발급한 저장소 ID.
        owner: 저장소 소유자 (org 또는 user login).
        name: 저장소 이름.
        installation_id: GitHub App Installation ID.
        is_active: 활성 여부.
    """

    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
        UniqueConstraint("github_repo_id", name="uq_repositories_github_repo_id"),
        Index("ix_repositories_owner_name", "owner", "name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    installation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills: Mapped[list["Skill"]] = relationship(  # noqa: F821
        "Skill", back_populates="repository", cascade="all, delete-orphan"
    )
    pull_requests: Mapped[list["PullRequest"]] = relationship(  # noqa: F821
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )
