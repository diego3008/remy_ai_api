from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.business import Businesses
    from src.models.dish import Dish


class Menu(TimestampMixin, Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80), default="Main")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurant: Mapped[Businesses] = relationship(back_populates="menus")
    dishes: Mapped[list[Dish]] = relationship(
        back_populates="menu", cascade="all, delete-orphan"
    )
