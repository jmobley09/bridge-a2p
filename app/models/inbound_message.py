from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class InboundMessage(SQLModel, table=True):
    __tablename__ = "inbound_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message_sid: str = Field(max_length=64, unique=True)
    account_sid: str | None = Field(default=None, max_length=64)
    from_number: str = Field(max_length=32, index=True)
    to_number: str = Field(max_length=32)
    body: str = Field(sa_column=Column(Text, nullable=False))
    num_media: int = Field(default=0)
    status: str = Field(default="received", max_length=32)
    raw_payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    received_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True),
    )
