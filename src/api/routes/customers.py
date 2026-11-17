from fastapi import APIRouter, Response, status
from sqlalchemy import select

from src.models import Businesses, Customer
from src.schemas import CustomerCreate, CustomerRead, CustomerUpdate

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[CustomerRead])
async def list_customers(
    session: SessionDep,
    page: PaginationDep,
    business_id: int | None = None,
    phone: str | None = None,
):
    stmt = select(Customer).order_by(Customer.id)
    if business_id is not None:
        stmt = stmt.where(Customer.business_id == business_id)
    if phone is not None:
        stmt = stmt.where(Customer.phone == phone)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(payload: CustomerCreate, session: SessionDep):
    await get_or_404(session, Businesses, payload.business_id)
    customer = Customer(**payload.model_dump())
    session.add(customer)
    await commit_or_409(session)  # duplicate (business_id, phone) -> 409
    await session.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(customer_id: int, session: SessionDep):
    return await get_or_404(session, Customer, customer_id)


@router.patch("/{customer_id}", response_model=CustomerRead)
async def update_customer(customer_id: int, payload: CustomerUpdate, session: SessionDep):
    customer = await get_or_404(session, Customer, customer_id)
    if apply_updates(customer, payload):
        await commit_or_409(session)
        await session.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, session: SessionDep):
    # Customers with orders RESTRICT -> 409.
    await delete_or_404(session, Customer, customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
