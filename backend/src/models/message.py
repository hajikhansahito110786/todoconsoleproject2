from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid


class MessageBase(SQLModel):
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id")
    role: str = Field(regex="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=10000)


class Message(MessageBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(MessageBase):
    pass


class MessageUpdate(SQLModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)


class MessageRead(MessageBase):
    id: uuid.UUID
    timestamp: datetime