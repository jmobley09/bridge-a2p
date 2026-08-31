from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class SendingListRecipient(SQLModel, table=True):
    __tablename__ = "sending_list_recipients"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    phone_number: str = Field(max_length=32, unique=True, index=True)
    active: bool = Field(default=True, index=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
