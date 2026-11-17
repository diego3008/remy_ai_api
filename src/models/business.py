from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
  from src.models.customer import Customer
  from src.models.menu import Menu
  from src.models.order import Order


class Businesses(Base):
  __tablename__ = "businesses"
  id: Mapped[int] = mapped_column(primary_key=True, index=True)
  name: Mapped[str]
  b_active: Mapped[bool]
  created_at: Mapped[datetime]
  updated_at: Mapped[datetime]
  phone: Mapped[str]
  timezone: Mapped[str] = mapped_column(String(64), default="America/Monterrey")
  menus: Mapped[list[Menu]] = relationship(back_populates="restaurant")
  customers: Mapped[list[Customer]] = relationship(back_populates="restaurant")
  orders: Mapped[list[Order]] = relationship(back_populates="restaurant")
