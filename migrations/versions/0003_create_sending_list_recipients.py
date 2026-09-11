"""create sending list recipients

Revision ID: 0003_sending_list
Revises: 0002_create_allowed_senders
Create Date: 2026-07-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_sending_list"
down_revision: Union[str, None] = "0002_create_allowed_senders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sending_list_recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number", name="uq_sending_list_recipients_phone_number"),
    )
    op.create_index(
        "ix_sending_list_recipients_phone_number",
        "sending_list_recipients",
        ["phone_number"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sending_list_recipients_phone_number",
        table_name="sending_list_recipients",
    )
    op.drop_table("sending_list_recipients")
