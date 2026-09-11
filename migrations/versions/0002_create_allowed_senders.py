"""create allowed senders

Revision ID: 0002_create_allowed_senders
Revises: 0001_create_inbound_messages
Create Date: 2026-07-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_allowed_senders"
down_revision: Union[str, None] = "0001_create_inbound_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "allowed_senders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number", name="uq_allowed_senders_phone_number"),
    )
    op.create_index("ix_allowed_senders_is_active", "allowed_senders", ["is_active"])
    op.create_index("ix_allowed_senders_phone_number", "allowed_senders", ["phone_number"])


def downgrade() -> None:
    op.drop_index("ix_allowed_senders_phone_number", table_name="allowed_senders")
    op.drop_index("ix_allowed_senders_is_active", table_name="allowed_senders")
    op.drop_table("allowed_senders")
