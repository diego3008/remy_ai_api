from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from .base import ORMModel


class DishCreate(BaseModel):
    menu_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    is_available: bool = True


class DishUpdate(BaseModel):
    # menu_id is updatable so a dish can be moved between menus.
    menu_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    is_available: bool | None = None


class DishRead(ORMModel):
    id: int
    menu_id: int
    name: str
    description: str | None
    price: Decimal
    is_available: bool
    created_at: datetime
    updated_at: datetime
