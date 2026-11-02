import logging
from functools import lru_cache
from typing import Any

from langgraph_sdk import get_client
from langgraph_sdk.client import LangGraphClient

from src.models import IncomingMessage
from src.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_agent_client() -> LangGraphClient:
    settings = get_settings()
    return get_client(url=settings.LANGGRAPH_API_URL, api_key=settings.LANGGRAPH_API_KEY or None)


async def _get_thread_id(chat_id: int) -> str:
    client = get_agent_client()

    # One LangGraph thread per Telegram chat, found by metadata rather than
    # a local table, since LangGraph is already the system of record for it.
    threads = await client.threads.search(metadata={"telegram_chat_id": chat_id}, limit=1)
    if threads:
        return threads[0]["thread_id"]

    thread = await client.threads.create(metadata={"telegram_chat_id": chat_id})
    return thread["thread_id"]


def _extract_reply(result: dict[str, Any]) -> str | None:
    for message in reversed(result.get("messages") or []):
        if message.get("type") == "ai" and message.get("content"):
            content = message["content"]
            return content if isinstance(content, str) else str(content)
    return None


async def run_agent(msg: IncomingMessage) -> str | None:
    """Send a user message to the LangGraph agent and wait for its reply.

    Uses a run-and-wait call rather than streaming since the webhook needs
    the final text to send back to Telegram in one response.
    """
    settings = get_settings()
    client = get_agent_client()
    thread_id = await _get_thread_id(msg.chat_id)

    try:
        result = await client.runs.wait(
            thread_id,
            settings.LANGGRAPH_ASSISTANT_ID,
            input={"messages": [{"role": "user", "content": msg.content}]},
        )
    except Exception:
        logger.exception("Agent run failed for chat %s", msg.chat_id)
        return None

    return _extract_reply(result)
