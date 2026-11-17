import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from .base import ORMModel


class ConversationCreate(BaseModel):
    chat_id: uuid.UUID
    thread_id: uuid.UUID
    parent_thread_id: uuid.UUID
    b_active: bool = True
    message_count: int = Field(default=0, ge=0)


class ConversationUpdate(BaseModel):
    thread_id: uuid.UUID | None = None
    parent_thread_id: uuid.UUID | None = None
    b_active: bool | None = None
    message_count: int | None = Field(default=None, ge=0)


class ConversationRead(ORMModel):
    id: int
    chat_id: uuid.UUID
    thread_id: uuid.UUID
    parent_thread_id: uuid.UUID
    b_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
