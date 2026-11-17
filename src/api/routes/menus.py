from fastapi import APIRouter, Response, status
from sqlalchemy import select

from src.models import Businesses, Menu
from src.schemas import MenuCreate, MenuRead, MenuUpdate

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/menus", tags=["Menus"])


@router.get("", response_model=list[MenuRead])
async def list_menus(
    session: SessionDep,
    page: PaginationDep,
    business_id: int | None = None,
    is_active: bool | None = None,
):
    stmt = select(Menu).order_by(Menu.id)
    if business_id is not None:
        stmt = stmt.where(Menu.business_id == business_id)
    if is_active is not None:
        stmt = stmt.where(Menu.is_active == is_active)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=MenuRead, status_code=status.HTTP_201_CREATED)
async def create_menu(payload: MenuCreate, session: SessionDep):
    await get_or_404(session, Businesses, payload.business_id)
    menu = Menu(**payload.model_dump())
    session.add(menu)
    await commit_or_409(session)
    await session.refresh(menu)
    return menu


@router.get("/{menu_id}", response_model=MenuRead)
async def get_menu(menu_id: int, session: SessionDep):
    return await get_or_404(session, Menu, menu_id)


@router.patch("/{menu_id}", response_model=MenuRead)
async def update_menu(menu_id: int, payload: MenuUpdate, session: SessionDep):
    menu = await get_or_404(session, Menu, menu_id)
    if apply_updates(menu, payload):
        await commit_or_409(session)
        await session.refresh(menu)
    return menu


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu(menu_id: int, session: SessionDep):
    # Dishes cascade in the DB; dishes referenced by orders RESTRICT -> 409.
    await delete_or_404(session, Menu, menu_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
