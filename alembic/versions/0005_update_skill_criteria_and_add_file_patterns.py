"""update_skill_criteria_and_add_file_patterns

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # criteria: JSONB -> TEXT (빈 객체는 NULL로, 나머지는 JSON 문자열로)
    op.alter_column(
        "skills",
        "criteria",
        type_=sa.Text,
        existing_type=JSONB,
        postgresql_using="CASE WHEN criteria = '{}'::jsonb THEN NULL ELSE criteria::text END",
        existing_nullable=False,
        nullable=True,
        server_default=None,
    )
    # file_patterns 컬럼 추가
    op.add_column(
        "skills",
        sa.Column("file_patterns", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("skills", "file_patterns")
    op.alter_column(
        "skills",
        "criteria",
        type_=JSONB,
        existing_type=sa.Text,
        postgresql_using="COALESCE(criteria::jsonb, '{}'::jsonb)",
        existing_nullable=True,
        nullable=False,
        server_default="{}",
    )
