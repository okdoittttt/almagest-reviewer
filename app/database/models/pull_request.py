"""PullRequest ORM 모델."""
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class PullRequest(Base, TimestampMixin):
    """GitHub Pull Request 정보.

    Attributes:
        id: 내부 PK.
        repository_id: 연결된 Repository FK.
        github_pr_id: GitHub에서 발급한 PR ID.
        pr_number: PR 번호 (저장소 내 고유).
        title: PR 제목.
        author_login: PR 작성자 GitHub login.
        head_sha: 리뷰 대상 HEAD 커밋 SHA.
        base_branch: 머지 대상 브랜치.
        head_branch: PR 소스 브랜치.
        state: PR 상태 (open/closed/merged).
        risk_level: 리스크 수준 (LOW/MEDIUM/HIGH).
        triage_priority: 트리아지 우선순위 (nullable).
    """

    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repository_id", "pr_number", name="uq_pull_requests_repo_pr"),
        Index("ix_pull_requests_repo_state", "repository_id", "state"),
        Index("ix_pull_requests_repo_triage", "repository_id", "triage_priority"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    github_pr_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(1000))
    author_login: Mapped[str | None] = mapped_column(String(255))
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    base_branch: Mapped[str | None] = mapped_column(String(255))
    head_branch: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    triage_priority: Mapped[int | None] = mapped_column(Integer)

    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="pull_requests"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review", back_populates="pull_request", cascade="all, delete-orphan"
    )
