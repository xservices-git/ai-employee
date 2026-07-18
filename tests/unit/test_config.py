"""Test config and types."""

from __future__ import annotations

from core.common.config import get_settings


def test_settings_singleton():
    """Settings should be cached singleton."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_defaults():
    """Default values should be sensible."""
    s = get_settings()
    assert s.app_env == "development"
    assert s.api_port == 8000
    assert s.ollama_model_classifier == "qwen2.5:4b"
    assert s.confidence_auto_execute == 0.70
    assert s.confidence_approval_required == 0.40
