from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    vinted_base_url: str = "https://www.vinted.it"
    scan_interval_minutes: int = 60
    backend_port: int = 8000

    # Ollama (local LLM for product clustering)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    clustering_batch_size: int = 15

    # Rate limiting
    vinted_max_requests_per_minute: int = 20
    vinted_delay_min: float = 2.0
    vinted_delay_max: float = 5.0

    # Session
    vinted_session_refresh_minutes: int = 25

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
