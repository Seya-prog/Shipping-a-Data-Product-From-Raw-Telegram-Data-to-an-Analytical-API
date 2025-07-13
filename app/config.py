"""Central configuration loader.
Loads environment variables from a `.env` file at project root using python-dotenv.
This runs at import time so that any module depending on env vars can just:
    from app.config import settings
`settings` is a `pydantic.BaseSettings` instance.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

# Determine project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

# Load variables if .env exists; silently ignore if not
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    # Telegram API
    api_id: int | None = Field(default=None, env=["TG_API_ID", "API_ID"])
    api_hash: str | None = Field(default=None, env=["TG_API_HASH", "API_HASH"])
    bot_token: str | None = Field(default=None, env=["TG_BOT_TOKEN", "BOT_TOKEN"])

    # Database
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "telegram_db"
    db_port: int = 5432
    db_host: str = "db"  # docker-compose service name

    class Config:
        case_sensitive = False
        env_file = ENV_FILE
        env_file_encoding = "utf-8"


settings = Settings()
