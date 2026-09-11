"""create inbound messages

Revision ID: 0001_create_inbound_messages
Revises:
Create Date: 2026-07-17 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_inbound_messages"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inbound_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_sid", sa.String(length=64), nullable=False),
        sa.Column("account_sid", sa.String(length=64), nullable=True),
        sa.Column("from_number", sa.String(length=32), nullable=False),
        sa.Column("to_number", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("num_media", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_sid", name="uq_inbound_messages_message_sid"),
    )
    op.create_index("ix_inbound_messages_from_number", "inbound_messages", ["from_number"])
    op.create_index("ix_inbound_messages_received_at", "inbound_messages", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_inbound_messages_received_at", table_name="inbound_messages")
    op.drop_index("ix_inbound_messages_from_number", table_name="inbound_messages")
    op.drop_table("inbound_messages")
