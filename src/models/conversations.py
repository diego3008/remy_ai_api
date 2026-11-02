import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from src.models import Base


class Conversations(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chat_id: Mapped[uuid.UUID]
    thread_id: Mapped[uuid.UUID]
    parent_thread_id: Mapped[uuid.UUID]
    created_at: Mapped[datetime]
    b_active: Mapped[bool]
    message_count: Mapped[int]
    updated_at: Mapped[datetime]