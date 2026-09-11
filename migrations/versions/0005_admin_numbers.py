"""rename allowed senders to admin numbers

Revision ID: 0005_admin_numbers
Revises: 0004_recipient_active
Create Date: 2026-08-31 00:00:00
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005_admin_numbers"
down_revision: Union[str, None] = "0004_recipient_active"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("allowed_senders", "admin_numbers")
    op.execute(
        "ALTER TABLE admin_numbers "
        "RENAME CONSTRAINT uq_allowed_senders_phone_number TO uq_admin_numbers_phone_number"
    )
    op.execute("ALTER INDEX ix_allowed_senders_is_active RENAME TO ix_admin_numbers_is_active")
    op.execute("ALTER INDEX ix_allowed_senders_phone_number RENAME TO ix_admin_numbers_phone_number")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE admin_numbers "
        "RENAME CONSTRAINT uq_admin_numbers_phone_number TO uq_allowed_senders_phone_number"
    )
    op.execute("ALTER INDEX ix_admin_numbers_is_active RENAME TO ix_allowed_senders_is_active")
    op.execute("ALTER INDEX ix_admin_numbers_phone_number RENAME TO ix_allowed_senders_phone_number")
    op.rename_table("admin_numbers", "allowed_senders")
