"""Config doc tu env - khong can file YAML phuc tap."""
from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str
    port: int
    log_level: str
    data_dir: Path
    workspace_dir: Path
    ollama_base_url: str
    ollama_model_plan: str
    ollama_model_exec: str
    ollama_model_review: str
    ollama_model_embed: str
    auto_approve_threshold: float


def load_settings() -> Settings:
    # Default DATA_DIR = <project_root>/data (absolute, not CWD-relative)
    _project_root = Path(__file__).resolve().parent.parent
    data = Path(os.getenv("DATA_DIR", str(_project_root / "data"))).resolve()
    work = Path(os.getenv("WORKSPACE_DIR", str(_project_root / "workspace"))).resolve()
    data.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    (data / "sqlite").mkdir(parents=True, exist_ok=True)
    return Settings(
        env=os.getenv("APP_ENV", "dev"),
        port=int(os.getenv("APP_PORT", "8000")),
        log_level=os.getenv("APP_LOG_LEVEL", "info"),
        data_dir=data,
        workspace_dir=work,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model_plan=os.getenv("OLLAMA_MODEL_PLAN", "qwen2.5:4b"),
        ollama_model_exec=os.getenv("OLLAMA_MODEL_EXEC", "qwen2.5:4b"),
        ollama_model_review=os.getenv("OLLAMA_MODEL_REVIEW", "qwen2.5:4b"),
        ollama_model_embed=os.getenv("OLLAMA_MODEL_EMBED", "nomic-embed-text"),
        auto_approve_threshold=float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.85")),
    )


SETTINGS = load_settings()
