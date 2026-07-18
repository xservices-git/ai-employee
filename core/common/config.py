"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings, loaded from .env file or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database
    database_url: str = "sqlite:///./data/ai-employee.db"

    # Vector store
    chroma_path: str = "./data/chroma"

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model_classifier: str = "qwen2.5:4b"
    ollama_model_planner: str = "llama3.1:8b"
    ollama_model_executor: str = "qwen2.5:4b"
    ollama_model_critic: str = "llama3.1:8b"
    ollama_model_curator: str = "qwen2.5:4b"
    ollama_model_embed: str = "nomic-embed-text:v1.5"
    ollama_model_rerank: str = "bge-reranker-base"

    # MCP servers
    mcp_data_processing_url: str = "stdio://./mcp-servers/data-processing/server.py"
    mcp_communication_url: str = "stdio://./mcp-servers/communication/server.py"

    # Communication
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # Web research
    web_search_provider: str = "duckduckgo"
    web_fetch_timeout: int = 30

    # Rate limiting
    rate_limit_per_user_hour: int = 100
    rate_limit_per_tool_hour: int = 1000
    rate_limit_global_hour: int = 10000

    # Confidence
    confidence_auto_execute: float = 0.70
    confidence_approval_required: float = 0.40

    # Observability
    otel_exporter_otlp_endpoint: str = ""
    prometheus_port: int = 9090

    # Workspace
    workspace_dir: Path = Path("./workspace")

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
