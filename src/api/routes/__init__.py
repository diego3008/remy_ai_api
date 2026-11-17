from fastapi import APIRouter

from . import businesses, conversations, customers, dishes, menus, orders

api_router = APIRouter(prefix="/api/v1")

for module in (businesses, menus, dishes, customers, orders, conversations):
    api_router.include_router(module.router)
