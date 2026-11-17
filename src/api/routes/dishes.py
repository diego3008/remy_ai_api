from fastapi import APIRouter, Response, status
from sqlalchemy import select

from src.models import Dish, Menu
from src.schemas import DishCreate, DishRead, DishUpdate

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/dishes", tags=["Dishes"])


@router.get("", response_model=list[DishRead])
async def list_dishes(
    session: SessionDep,
    page: PaginationDep,
    menu_id: int | None = None,
    business_id: int | None = None,
    is_available: bool | None = None,
):
    stmt = select(Dish).order_by(Dish.id)
    if menu_id is not None:
        stmt = stmt.where(Dish.menu_id == menu_id)
    if business_id is not None:
        stmt = stmt.join(Menu).where(Menu.business_id == business_id)
    if is_available is not None:
        stmt = stmt.where(Dish.is_available == is_available)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=DishRead, status_code=status.HTTP_201_CREATED)
async def create_dish(payload: DishCreate, session: SessionDep):
    await get_or_404(session, Menu, payload.menu_id)
    dish = Dish(**payload.model_dump())
    session.add(dish)
    await commit_or_409(session)
    await session.refresh(dish)
    return dish


@router.get("/{dish_id}", response_model=DishRead)
async def get_dish(dish_id: int, session: SessionDep):
    return await get_or_404(session, Dish, dish_id)


@router.patch("/{dish_id}", response_model=DishRead)
async def update_dish(dish_id: int, payload: DishUpdate, session: SessionDep):
    dish = await get_or_404(session, Dish, dish_id)
    if payload.menu_id is not None and payload.menu_id != dish.menu_id:
        await get_or_404(session, Menu, payload.menu_id)
    if apply_updates(dish, payload):
        await commit_or_409(session)
        await session.refresh(dish)
    return dish


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(dish_id: int, session: SessionDep):
    # Dishes referenced by order items RESTRICT -> 409; mark unavailable instead.
    await delete_or_404(session, Dish, dish_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
