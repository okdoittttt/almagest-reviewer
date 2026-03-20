"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # repositories
    op.create_table(
        "repositories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("installation_id", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_repo_id", name="uq_repositories_github_repo_id"),
        sa.UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )
    op.create_index("ix_repositories_owner_name", "repositories", ["owner", "name"])

    # skills
    op.create_table(
        "skills",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criteria", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "name", name="uq_skills_repository_name"),
    )
    op.create_index("ix_skills_repository_enabled", "skills", ["repository_id", "is_enabled"])

    # pull_requests
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("github_pr_id", sa.BigInteger(), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(1000), nullable=True),
        sa.Column("author_login", sa.String(255), nullable=True),
        sa.Column("head_sha", sa.String(40), nullable=False),
        sa.Column("base_branch", sa.String(255), nullable=True),
        sa.Column("head_branch", sa.String(255), nullable=True),
        sa.Column("state", sa.String(50), nullable=False, server_default="open"),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("triage_priority", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "pr_number", name="uq_pull_requests_repo_pr"),
    )
    op.create_index("ix_pull_requests_repo_state", "pull_requests", ["repository_id", "state"])
    op.create_index("ix_pull_requests_repo_triage", "pull_requests", ["repository_id", "triage_priority"])

    # reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("pull_request_id", sa.BigInteger(), nullable=False),
        sa.Column("head_sha", sa.String(40), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("pr_intent", postgresql.JSONB(), nullable=True),
        sa.Column("risk_assessment", postgresql.JSONB(), nullable=True),
        sa.Column("file_reviews", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("final_review", sa.Text(), nullable=True),
        sa.Column("review_decision", sa.String(50), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_pull_request_created", "reviews", ["pull_request_id", "created_at"])
    op.create_index("ix_reviews_head_sha", "reviews", ["head_sha"])

    # review_comments
    op.create_table(
        "review_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("review_id", sa.BigInteger(), nullable=False),
        sa.Column("filename", sa.String(1000), nullable=True),
        sa.Column("comment_type", sa.String(50), nullable=False, server_default="issue"),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_addressed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("addressed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_comments_review_id", "review_comments", ["review_id"])
    op.create_index("ix_review_comments_review_addressed", "review_comments", ["review_id", "is_addressed"])


def downgrade() -> None:
    op.drop_table("review_comments")
    op.drop_table("reviews")
    op.drop_table("pull_requests")
    op.drop_table("skills")
    op.drop_table("repositories")
