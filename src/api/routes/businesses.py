from fastapi import APIRouter, Response, status
from sqlalchemy import func, select

from src.models import Businesses
from src.schemas import BusinessCreate, BusinessRead, BusinessUpdate

from ._common import (
    PaginationDep,
    SessionDep,
    apply_updates,
    commit_or_409,
    delete_or_404,
    get_or_404,
)

router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.get("", response_model=list[BusinessRead])
async def list_businesses(
    session: SessionDep, page: PaginationDep, b_active: bool | None = None
):
    stmt = select(Businesses).order_by(Businesses.id)
    if b_active is not None:
        stmt = stmt.where(Businesses.b_active == b_active)
    result = await session.scalars(stmt.offset(page.offset).limit(page.limit))
    return result.all()


@router.post("", response_model=BusinessRead, status_code=status.HTTP_201_CREATED)
async def create_business(payload: BusinessCreate, session: SessionDep):
    # The businesses table has no server-side timestamp defaults, so set them here.
    business = Businesses(
        **payload.model_dump(), created_at=func.now(), updated_at=func.now()
    )
    session.add(business)
    await commit_or_409(session)
    await session.refresh(business)
    return business


@router.get("/{business_id}", response_model=BusinessRead)
async def get_business(business_id: int, session: SessionDep):
    return await get_or_404(session, Businesses, business_id)


@router.patch("/{business_id}", response_model=BusinessRead)
async def update_business(business_id: int, payload: BusinessUpdate, session: SessionDep):
    business = await get_or_404(session, Businesses, business_id)
    if apply_updates(business, payload):
        business.updated_at = func.now()
        await commit_or_409(session)
        await session.refresh(business)
    return business


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(business_id: int, session: SessionDep):
    # Menus and customers cascade; existing orders RESTRICT -> 409.
    await delete_or_404(session, Businesses, business_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
