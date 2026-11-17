from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, Money, TimestampMixin
from src.models.enums import Channel, Fulfillment, OrderStatus, _enum

if TYPE_CHECKING:
    from src.models.business import Businesses
    from src.models.customer import Customer
    from src.models.order_item import OrderItem


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "fulfillment != 'delivery' OR delivery_address IS NOT NULL",
            name="ck_order_delivery_needs_address",
        ),
        Index("ix_orders_business_status", "business_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="RESTRICT")
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    channel: Mapped[Channel] = mapped_column(_enum(Channel, "order_channel"))
    fulfillment: Mapped[Fulfillment] = mapped_column(
        _enum(Fulfillment, "order_fulfillment")
    )
    status: Mapped[OrderStatus] = mapped_column(
        _enum(OrderStatus, "order_status"), default=OrderStatus.PENDING
    )
    delivery_address: Mapped[str | None] = mapped_column(Text)
    total: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    # LangGraph thread that produced this order (state lives in the checkpointer).
    thread_id: Mapped[str | None] = mapped_column(String(128), index=True)

    restaurant: Mapped[Businesses] = relationship(back_populates="orders")
    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def recalculate_total(self) -> Decimal:
        self.total = sum(
            (item.unit_price * item.quantity for item in self.items), Decimal("0.00")
        )
        return self.total
