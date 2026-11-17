from datetime import datetime

from pydantic import BaseModel, Field

from .base import ORMModel


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    b_active: bool = True
    timezone: str = Field(default="America/Monterrey", max_length=64)


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = Field(default=None, min_length=1)
    b_active: bool | None = None
    timezone: str | None = Field(default=None, max_length=64)


class BusinessRead(ORMModel):
    id: int
    name: str
    phone: str
    b_active: bool
    timezone: str
    created_at: datetime
    updated_at: datetime
