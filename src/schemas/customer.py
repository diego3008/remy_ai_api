from datetime import datetime

from pydantic import BaseModel, Field

from .base import ORMModel


class CustomerCreate(BaseModel):
    business_id: int
    phone: str = Field(min_length=1, max_length=20)  # E.164, e.g. +528112345678
    name: str | None = Field(default=None, max_length=120)
    default_address: str | None = None


class CustomerUpdate(BaseModel):
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=120)
    default_address: str | None = None


class CustomerRead(ORMModel):
    id: int
    business_id: int
    phone: str
    name: str | None
    default_address: str | None
    created_at: datetime
    updated_at: datetime
