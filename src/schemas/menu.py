from datetime import datetime

from pydantic import BaseModel, Field

from .base import ORMModel


class MenuCreate(BaseModel):
    business_id: int
    name: str = Field(default="Main", min_length=1, max_length=80)
    is_active: bool = True


class MenuUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    is_active: bool | None = None


class MenuRead(ORMModel):
    id: int
    business_id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
