from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.business import Businesses
    from src.models.order import Order


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        # A phone number identifies one customer per restaurant.
        UniqueConstraint("business_id", "phone", name="uq_customer_business_phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE")
    )
    phone: Mapped[str] = mapped_column(String(20))  # E.164, e.g. +528112345678
    name: Mapped[str | None] = mapped_column(String(120))
    default_address: Mapped[str | None] = mapped_column(Text)

    restaurant: Mapped[Businesses] = relationship(back_populates="customers")
    orders: Mapped[list[Order]] = relationship(back_populates="customer")
