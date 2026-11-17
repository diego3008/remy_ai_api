from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models.enums import Channel, Fulfillment, OrderStatus

from .base import ORMModel


class OrderItemCreate(BaseModel):
    dish_id: int
    quantity: int = Field(default=1, gt=0)
    notes: str | None = None


class OrderItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    notes: str | None = None


class OrderItemRead(ORMModel):
    id: int
    order_id: int
    dish_id: int
    quantity: int
    unit_price: Decimal
    notes: str | None


class OrderCreate(BaseModel):
    business_id: int
    customer_id: int
    channel: Channel
    fulfillment: Fulfillment
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: str | None = None
    thread_id: str | None = Field(default=None, max_length=128)
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    channel: Channel | None = None
    fulfillment: Fulfillment | None = None
    status: OrderStatus | None = None
    delivery_address: str | None = None
    thread_id: str | None = Field(default=None, max_length=128)


class OrderRead(ORMModel):
    id: int
    business_id: int
    customer_id: int
    channel: Channel
    fulfillment: Fulfillment
    status: OrderStatus
    delivery_address: str | None
    total: Decimal
    thread_id: str | None
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime
