from __future__ import annotations

import logging
from functools import lru_cache
import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-3.5-turbo", alias="OPENROUTER_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", alias="ANTHROPIC_MODEL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-2.0-flash", alias="GOOGLE_MODEL")
    perplexity_api_key: str | None = Field(default=None, alias="PERPLEXITY_API_KEY")
    perplexity_model: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="mixtral-8x7b-32768", alias="GROQ_MODEL")
    together_api_key: str | None = Field(default=None, alias="TOGETHER_API_KEY")
    together_model: str = Field(default="mistralai/Mixtral-8x22B-Instruct-v0.1", alias="TOGETHER_MODEL")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    mistral_api_key: str | None = Field(default=None, alias="MISTRAL_API_KEY")
    mistral_model: str = Field(default="mistral-large-latest", alias="MISTRAL_MODEL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_search_results: int = Field(default=10, alias="MAX_SEARCH_RESULTS")
    # Increased context limit to allow for richer PDF extraction
    max_context_chars: int = Field(default=12000, alias="MAX_CONTEXT_CHARS")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    tavily_topic: str = Field(default="general", alias="TAVILY_TOPIC")
    
    # Deterministic mode settings
    default_seed: int = Field(default=42, alias="DEFAULT_SEED")
    default_temperature: float = Field(default=0.2, alias="DEFAULT_TEMPERATURE")
    default_top_p: float = Field(default=0.9, alias="DEFAULT_TOP_P")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


class LogConfig:
    """Helper responsible for configuring structlog and stdlib logging."""

    def __init__(self, level: str = "INFO") -> None:
        self.level = level.upper()

    def configure(self) -> None:
        numeric_level = logging.getLevelName(self.level)
        if isinstance(numeric_level, str):
            numeric_level = logging.INFO

        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


def configure_logging(settings: Settings | None = None) -> None:
    """Initialize logging using the provided settings."""

    config = LogConfig(level=(settings or get_settings()).log_level)
    config.configure()
