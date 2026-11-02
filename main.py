import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import Application
from src.api import telegram_router
from src.config import get_settings
from src.db import get_engine

logging.basicConfig(
    level="INFO",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
SETTINGS = get_settings()

def build_ptb() -> Application:
    return (
        Application.builder()
        .token(SETTINGS.TELEGRAM_BOT_TOKEN)
        .updater(None)
        .build()
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    ptb = build_ptb()
    app.state.ptb = ptb

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

    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()
    
    await get_engine().dispose()


app = FastAPI(
    title="Telegram Gateway",
    description="Receives Telegram updates and forwards them to the agent service.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(telegram_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
