from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration loaded from env vars / .env file."""

    anthropic_api_key: str = ""
    database_path: str = "data/fin_review.db"
    data_dir: str = "data"

    # Collector settings
    collector_interval_minutes: int = 120
    collector_user_agent: str = "FinReview/1.0"

    # Processor settings
    llm_model: str = "claude-sonnet-4-20250514"
    llm_batch_size: int = 10
    llm_rate_limit_per_minute: int = 3

    # Web settings
    web_host: str = "127.0.0.1"
    web_port: int = 8765

    model_config = {"env_prefix": "FIN_", "env_file": ".env"}
