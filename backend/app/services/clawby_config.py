"""Runtime Clawby API key management — file-backed, no restart needed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


def _config_path() -> Path:
    return Path(settings.data_dir) / "clawby_config.json"


def load_config() -> dict[str, Any]:
    path = _config_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    # Fall back to .env value
    return {"api_key": settings.clawby_api_key}


def save_config(data: dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_api_key() -> str:
    cfg = load_config()
    return cfg.get("api_key", "")


def update_api_key(new_key: str) -> None:
    cfg = load_config()
    cfg["api_key"] = new_key
    save_config(cfg)
