"""add_comment_parent_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "review_comments",
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_review_comments_parent_id",
        "review_comments",
        "review_comments",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_review_comments_parent_id", "review_comments", type_="foreignkey")
    op.drop_column("review_comments", "parent_id")
