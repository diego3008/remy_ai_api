from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, Money

if TYPE_CHECKING:
    from src.models.dish import Dish
    from src.models.order import Order


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    # Price snapshot at order time; later menu price changes don't affect it.
    unit_price: Mapped[Decimal] = mapped_column(Money)
    notes: Mapped[str | None] = mapped_column(Text)  # e.g. "no onions"

    order: Mapped[Order] = relationship(back_populates="items")
    dish: Mapped[Dish] = relationship()
