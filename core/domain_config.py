"""Domain config loader - YAML files from domain_configs/ dir.

Reads from domain_configs/<domain>/rules.yaml.
If file not found, returns sensible defaults.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_CONFIGS_DIR: Optional[Path] = None

def set_configs_dir(path: Path) -> None:
    global _CONFIGS_DIR
    _CONFIGS_DIR = path

def get_configs_dir() -> Path:
    global _CONFIGS_DIR
    if _CONFIGS_DIR:
        return _CONFIGS_DIR
    return ROOT / "domain_configs"

def list_domains() -> list[str]:
    """List available domains (subdirs of domain_configs/)."""
    d = get_configs_dir()
    if not d.exists():
        return []
    return sorted(
        p.name for p in d.iterdir()
        if p.is_dir() and not p.name.startswith("_") and not p.name.startswith(".")
    )

def get_rules(domain: str) -> list[dict]:
    """Load rules.yaml for a domain. Returns [] if not found."""
    path = get_configs_dir() / domain / "rules.yaml"
    if not path.exists():
        return []
    import yaml  # optional dep
    try:
        with open(str(path)) as f:
            data = yaml.safe_load(f) or {}
            return data.get("rules", [])
    except Exception:
        return []

def get_config(domain: str, key: str, default=None):
    """Get a config value from domain_configs/<domain>/config.yaml or config.json.
    Supports nested keys: 'config.default_currency' digs into config dict."""
    path = get_configs_dir() / domain / "config.yaml"
    if not path.exists():
        path = get_configs_dir() / domain / "config.json"
    if not path.exists():
        return default
    try:
        if path.suffix == ".yaml":
            import yaml
            with open(str(path)) as f:
                data = yaml.safe_load(f) or {}
        else:
            import json
            with open(str(path)) as f:
                data = json.load(f) or {}
        # Support nested access: key = "config.default_currency" -> data["config"]["default_currency"]
        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return default
        return current
    except Exception:
        return default
