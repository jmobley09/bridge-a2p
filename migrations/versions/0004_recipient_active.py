"""add active flag to sending list recipients

Revision ID: 0004_recipient_active
Revises: 0003_sending_list
Create Date: 2026-08-31 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_recipient_active"
down_revision: Union[str, None] = "0003_sending_list"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sending_list_recipients",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_sending_list_recipients_active",
        "sending_list_recipients",
        ["active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sending_list_recipients_active",
        table_name="sending_list_recipients",
    )
    op.drop_column("sending_list_recipients", "active")
