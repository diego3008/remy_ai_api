import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select

from src.models import Conversations
from src.schemas import ConversationCreate, ConversationRead, ConversationUpdate

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    session: SessionDep,
    page: PaginationDep,
    chat_id: uuid.UUID | None = None,
    b_active: bool | None = None,
):
    stmt = select(Conversations).order_by(Conversations.id)
    if chat_id is not None:
        stmt = stmt.where(Conversations.chat_id == chat_id)
    if b_active is not None:
        stmt = stmt.where(Conversations.b_active == b_active)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, session: SessionDep):
    # The conversations table has no server-side timestamp defaults, so set them here.
    conversation = Conversations(
        **payload.model_dump(), created_at=func.now(), updated_at=func.now()
    )
    session.add(conversation)
    await commit_or_409(session)
    await session.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: int, session: SessionDep):
    return await get_or_404(session, Conversations, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int, payload: ConversationUpdate, session: SessionDep
):
    conversation = await get_or_404(session, Conversations, conversation_id)
    if apply_updates(conversation, payload):
        conversation.updated_at = func.now()
        await commit_or_409(session)
        await session.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int, session: SessionDep):
    await delete_or_404(session, Conversations, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
