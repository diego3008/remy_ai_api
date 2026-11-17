from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, Money, TimestampMixin

if TYPE_CHECKING:
    from src.models.menu import Menu


class Dish(TimestampMixin, Base):
    __tablename__ = "dishes"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_dish_price_nonnegative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Money)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    menu: Mapped[Menu] = relationship(back_populates="dishes")
