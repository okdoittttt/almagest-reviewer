"""add_dismiss_and_effective_risk

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # review_comments: severity + dismiss 관련 필드 추가
    op.add_column("review_comments", sa.Column("severity", sa.String(20), nullable=True))
    op.add_column("review_comments", sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("review_comments", sa.Column("dismissed_reason", sa.Text(), nullable=True))
    op.add_column("review_comments", sa.Column("dismissed_by", sa.String(255), nullable=True))
    op.add_column("review_comments", sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index(
        "ix_review_comments_review_dismissed",
        "review_comments",
        ["review_id", "is_dismissed"],
    )

    # reviews: effective_risk 필드 추가
    op.add_column("reviews", sa.Column("effective_risk_score", sa.Float(), nullable=True))
    op.add_column("reviews", sa.Column("effective_risk_level", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "effective_risk_level")
    op.drop_column("reviews", "effective_risk_score")

    op.drop_index("ix_review_comments_review_dismissed", table_name="review_comments")
    op.drop_column("review_comments", "dismissed_at")
    op.drop_column("review_comments", "dismissed_by")
    op.drop_column("review_comments", "dismissed_reason")
    op.drop_column("review_comments", "is_dismissed")
    op.drop_column("review_comments", "severity")
