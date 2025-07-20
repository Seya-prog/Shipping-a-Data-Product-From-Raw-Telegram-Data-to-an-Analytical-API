"""Central configuration loader.
Loads environment variables from a `.env` file at project root using python-dotenv.
Access via:

    from src.config import settings

This file was moved from `app/config.py` to keep all library code under `src/`.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

# Determine project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

# Load variables if .env exists; silently ignore if not
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    # Telegram API
    api_id: int | None = Field(default=None, validation_alias=AliasChoices("TG_API_ID", "API_ID"))
    api_hash: str | None = Field(default=None, validation_alias=AliasChoices("TG_API_HASH", "API_HASH"))
    bot_token: str | None = Field(default=None, validation_alias=AliasChoices("TG_BOT_TOKEN", "BOT_TOKEN"))

    # Database
    postgres_user: str = "telegram"
    postgres_password: str = "Seyaman@123"
    postgres_db: str = "telegram_dw"
    db_port: int = 5432
    db_host: str = "localhost"  # docker-compose service name




settings = Settings()
