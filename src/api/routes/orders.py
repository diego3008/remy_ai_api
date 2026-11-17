from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Businesses, Customer, Dish, Menu, Order, OrderItem
from src.models.enums import Fulfillment, OrderStatus
from src.schemas import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderItemUpdate,
    OrderRead,
    OrderUpdate,
)

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


async def _load_order(session: AsyncSession, order_id: int) -> Order:
    """Fetch an order with its items eagerly loaded (async can't lazy-load)."""
    order = await session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
        .execution_options(populate_existing=True)
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Order {order_id} not found")
    return order


async def _build_item(
    session: AsyncSession, business_id: int, item: OrderItemCreate
) -> OrderItem:
    """Validate the dish belongs to the business and snapshot its current price."""
    row = (
        await session.execute(
            select(Dish, Menu.business_id).join(Menu).where(Dish.id == item.dish_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Dish {item.dish_id} not found")
    dish, dish_business_id = row
    if dish_business_id != business_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Dish {dish.id} does not belong to business {business_id}",
        )
    if not dish.is_available:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Dish {dish.id} is not available"
        )
    return OrderItem(
        dish_id=dish.id, quantity=item.quantity, notes=item.notes, unit_price=dish.price
    )


def _check_delivery_address(order: Order) -> None:
    if order.fulfillment == Fulfillment.DELIVERY and not order.delivery_address:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "delivery_address is required for delivery orders",
        )


@router.get("", response_model=list[OrderRead])
async def list_orders(
    session: SessionDep,
    page: PaginationDep,
    business_id: int | None = None,
    customer_id: int | None = None,
    status_: Annotated[OrderStatus | None, Query(alias="status")] = None,
    thread_id: str | None = None,
):
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.id.desc())
    if business_id is not None:
        stmt = stmt.where(Order.business_id == business_id)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if status_ is not None:
        stmt = stmt.where(Order.status == status_)
    if thread_id is not None:
        stmt = stmt.where(Order.thread_id == thread_id)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, session: SessionDep):
    await get_or_404(session, Businesses, payload.business_id)
    customer = await get_or_404(session, Customer, payload.customer_id)
    if customer.business_id != payload.business_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Customer {customer.id} does not belong to business {payload.business_id}",
        )

    items = [await _build_item(session, payload.business_id, i) for i in payload.items]
    order = Order(**payload.model_dump(exclude={"items"}), items=items)
    if order.fulfillment == Fulfillment.DELIVERY and not order.delivery_address:
        order.delivery_address = customer.default_address
    _check_delivery_address(order)
    order.recalculate_total()

    session.add(order)
    await commit_or_409(session)
    return await _load_order(session, order.id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, session: SessionDep):
    return await _load_order(session, order_id)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(order_id: int, payload: OrderUpdate, session: SessionDep):
    order = await _load_order(session, order_id)
    if apply_updates(order, payload):
        _check_delivery_address(order)
        await commit_or_409(session)
        order = await _load_order(session, order_id)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, session: SessionDep):
    # Items cascade in the DB.
    await delete_or_404(session, Order, order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Order items (nested; every change recalculates the order total) ---


def _find_item(order: Order, item_id: int) -> OrderItem:
    for item in order.items:
        if item.id == item_id:
            return item
    raise HTTPException(
        status.HTTP_404_NOT_FOUND, f"OrderItem {item_id} not found in order {order.id}"
    )


@router.get("/{order_id}/items", response_model=list[OrderItemRead])
async def list_order_items(order_id: int, session: SessionDep):
    return (await _load_order(session, order_id)).items


@router.post(
    "/{order_id}/items", response_model=OrderRead, status_code=status.HTTP_201_CREATED
)
async def add_order_item(order_id: int, payload: OrderItemCreate, session: SessionDep):
    order = await _load_order(session, order_id)
    order.items.append(await _build_item(session, order.business_id, payload))
    order.recalculate_total()
    await commit_or_409(session)
    return await _load_order(session, order_id)


@router.patch("/{order_id}/items/{item_id}", response_model=OrderRead)
async def update_order_item(
    order_id: int, item_id: int, payload: OrderItemUpdate, session: SessionDep
):
    order = await _load_order(session, order_id)
    if apply_updates(_find_item(order, item_id), payload):
        order.recalculate_total()
        await commit_or_409(session)
        order = await _load_order(session, order_id)
    return order


@router.delete("/{order_id}/items/{item_id}", response_model=OrderRead)
async def delete_order_item(order_id: int, item_id: int, session: SessionDep):
    order = await _load_order(session, order_id)
    order.items.remove(_find_item(order, item_id))  # delete-orphan removes the row
    order.recalculate_total()
    await commit_or_409(session)
    return await _load_order(session, order_id)
