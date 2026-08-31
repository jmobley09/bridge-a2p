from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class AdminNumber(SQLModel, table=True):
    __tablename__ = "admin_numbers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    phone_number: str = Field(max_length=32, unique=True, index=True)
    label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    is_active: bool = Field(default=True, index=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )
