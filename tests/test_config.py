from src.config import Settings

REQUIRED = dict(
    TELEGRAM_BOT_TOKEN="1:abc",
    TELEGRAM_WEBHOOK_SECRET="secret",
    LANGGRAPH_API_URL="http://localhost:2024",
    DB_USER="u",
    DB_PASSWORD="p",
    DB_HOST="localhost",
    DB_PORT=5432,
    DB_NAME="n",
    WEBHOOK_URL="https://example.com",
)


def test_default_assistant_id_matches_remy_ai_graph(monkeypatch):
    # remy_ai registers its graph as "main_graph" in langgraph.json
    monkeypatch.delenv("LANGGRAPH_ASSISTANT_ID", raising=False)
    settings = Settings(_env_file=None, **REQUIRED)
    assert settings.LANGGRAPH_ASSISTANT_ID == "main_graph"
