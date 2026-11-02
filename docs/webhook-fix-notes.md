# Fix: Telegram flood control crash on `fastapi dev`

## Problem

`fastapi dev` auto-reloads on file changes, re-running the FastAPI `lifespan`
on every reload. The lifespan unconditionally called `set_webhook` each time,
and Telegram rate-limits that endpoint hard. Repeated reloads triggered
flood control (`429 Too Many Requests` / `RetryAfter`), which wasn't caught,
so the app crashed on startup.

A second, unrelated bug was found on shutdown: the wrong object had
`.dispose()` called on it.

## Change 1: Only re-register the webhook when it actually changed

**Before**

```python
webhook_url = f"{SETTINGS.WEBHOOK_URL}/webhook/telegram"
await ptb.bot.set_webhook(
    url=webhook_url,
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True,
)
logger.info("Webhook registered: %s", webhook_url)
```

**After**

```python
webhook_url = f"{SETTINGS.WEBHOOK_URL}/webhook/telegram"
current = await ptb.bot.get_webhook_info()
if current.url != webhook_url:
    try:
        await ptb.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("Webhook registered: %s", webhook_url)
    except RetryAfter as e:
        logger.warning(
            "Telegram flood control hit while setting webhook; skipping re-registration (retry_after=%s)",
            e.retry_after,
        )
else:
    logger.info("Webhook already registered: %s", webhook_url)
```

**Why:** checks the currently registered webhook via `get_webhook_info()`
first, and skips `set_webhook` entirely if it's already pointing at the
right URL — so reloads stop hammering Telegram's rate-limited endpoint. If
flood control is still hit (e.g. first run after many reloads), the
`RetryAfter` exception is caught and logged as a warning instead of
crashing startup.

Also required a new import:

```python
from telegram.error import RetryAfter
```

## Change 2: Fix the shutdown disposal bug

**Before**

```python
await get_settings.dispose()
```

This called `.dispose()` on the `get_settings` function itself, not an
engine instance — would raise `AttributeError` on every shutdown.

**After**

```python
await get_engine().dispose()
```

**Why:** `get_engine()` (from `src/db.py`) returns the SQLAlchemy
`AsyncEngine`, which is the thing that actually needs disposing on
shutdown.
