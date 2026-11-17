# REMY AI API

This is the API project for the REMY AI agent. This API contains the routes and endpoints that the AI agent is going to consume with its tools making HTTP requests.

---

## **Technologies**

- Python
- FASTAPI
- SQLAlchemy
- Alembic
- PostgreSQL

---

## **Project Structure**

```
.
├── main.py                     # FastAPI app: lifespan (Telegram webhook setup), mounts routers, /health
├── pyproject.toml              # Dependencies (uv) and pytest config
├── alembic.ini
├── alembic/
│   ├── env.py                  # Uses Settings.sync_database_url (psycopg)
│   └── versions/               # Migrations: conversations, businesses, phone, menu/dish/customer/order
├── docs/
│   └── webhook-fix-notes.md    # Notes on the Telegram flood-control fix
├── src/
│   ├── config.py               # Pydantic Settings loaded from .env (Telegram, LangGraph, DB, webhook URL)
│   ├── db.py                   # Async engine, sessionmaker, get_session() FastAPI dependency
│   ├── api/
│   │   ├── __init__.py         # Exports api_router and telegram_router
│   │   ├── telegram.py         # POST /webhook/telegram: normalizes updates, replies via bot
│   │   ├── agent_client.py     # LangGraph SDK client: thread lookup per chat, run-and-wait
│   │   └── routes/             # REST CRUD, all mounted under /api/v1
│   │       ├── __init__.py     # Builds api_router from the resource routers
│   │       ├── _common.py      # SessionDep, pagination, get_or_404, commit_or_409, delete_or_404, apply_updates
│   │       ├── businesses.py
│   │       ├── menus.py
│   │       ├── dishes.py
│   │       ├── customers.py
│   │       ├── orders.py       # Orders + nested /orders/{id}/items (price snapshot, total recalculation)
│   │       └── conversations.py
│   ├── models/                 # SQLAlchemy 2.0 ORM models (Mapped / mapped_column)
│   │   ├── base.py             # Base, TimestampMixin, Money = Numeric(10, 2)
│   │   ├── enums.py            # Channel, Fulfillment, OrderStatus (stored as values in named PG enums)
│   │   ├── business.py         # Businesses
│   │   ├── menu.py             # Menu (belongs to business)
│   │   ├── dish.py             # Dish (belongs to menu)
│   │   ├── customer.py         # Customer (unique phone per business)
│   │   ├── order.py            # Order (+ recalculate_total)
│   │   ├── order_item.py       # OrderItem (unit_price snapshot)
│   │   ├── conversations.py    # Conversations
│   │   └── incoming_message.py # Pydantic: IncomingMessage / AgentResponse (not a DB table)
│   └── schemas/                # Pydantic request/response models: <Model>Create / Update / Read
│       ├── base.py             # ORMModel (from_attributes=True)
│       ├── business.py
│       ├── menu.py
│       ├── dish.py
│       ├── customer.py
│       ├── order.py            # Order + OrderItem schemas
│       └── conversation.py
└── tests/
    ├── conftest.py             # httpx client fixture; in-memory SQLite, or Postgres via TEST_DATABASE_URL
    └── test_crud.py            # CRUD and order-flow tests
```

---
### Adding a new resource
1. Add the model in `src/models/`, export it from `src/models/__init__.py`, then run `uv run alembic revision --autogenerate -m "..."`.
2. Add `Create` / `Update` / `Read` schemas in `src/schemas/` and export them from `src/schemas/__init__.py`.
3. Add a router in `src/api/routes/` using the helpers in `_common.py`, and register it in `src/api/routes/__init__.py`.
4. Add tests in `tests/`. Run them with `uv run pytest`
