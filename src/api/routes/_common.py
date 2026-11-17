from typing import Annotated, Any, TypeVar

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.db import get_session

ModelT = TypeVar("ModelT", bound=DeclarativeBase)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class Pagination(BaseModel):
    offset: int
    limit: int


def pagination(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Pagination:
    return Pagination(offset=offset, limit=limit)


PaginationDep = Annotated[Pagination, Depends(pagination)]


async def get_or_404(
    session: AsyncSession, model: type[ModelT], obj_id: int, *options: Any
) -> ModelT:
    obj = await session.get(model, obj_id, options=options or None)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} {obj_id} not found",
        )
    return obj


async def _conflict(session: AsyncSession, exc: IntegrityError) -> HTTPException:
    await session.rollback()
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Constraint violation: {exc.orig}",
    )


async def commit_or_409(session: AsyncSession) -> None:
    """Commit, translating constraint violations (unique, FK, checks) to 409."""
    try:
        await session.commit()
    except IntegrityError as exc:
        raise await _conflict(session, exc) from exc


async def delete_or_404(session: AsyncSession, model: type[ModelT], obj_id: int) -> None:
    """Delete a row by primary key with a Core DELETE.

    Core (not session.delete) so the DB's ON DELETE rules decide: CASCADE
    children go with it, RESTRICT references yield 409, rather than the ORM
    trying to null out NOT NULL child FKs.
    """
    try:
        result = await session.execute(delete(model).where(model.id == obj_id))
    except IntegrityError as exc:
        raise await _conflict(session, exc) from exc
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} {obj_id} not found",
        )
    await commit_or_409(session)


def apply_updates(obj: DeclarativeBase, payload: BaseModel) -> dict[str, Any]:
    """Copy explicitly-sent fields onto obj.

    Rejects an explicit null on a NOT NULL column with 422 instead of letting
    it reach the database.
    """
    changes = payload.model_dump(exclude_unset=True)
    columns = inspect(type(obj)).columns
    for field, value in changes.items():
        if value is None and not columns[field].nullable:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{field}' cannot be null",
            )
        setattr(obj, field, value)
    return changes
