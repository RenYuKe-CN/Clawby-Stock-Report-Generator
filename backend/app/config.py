"""Application configuration via pydantic-settings.

Load order: defaults → `.env` file → environment variables.
Runtime overrides (Provider / Template CRUD) are stored as JSON files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Service ports ──────────────────────────────────────────────────────
    backend_port: int = 8000
    frontend_port: int = 3000

    # ── Clawby ─────────────────────────────────────────────────────────────
    clawby_api_key: str = ""
    clawby_base_url: str = "https://api.openclawby.com"

    # ── Default LLM provider (imported into the provider registry at boot) ─
    llm_provider_type: str = "openai"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    # ── Default language ───────────────────────────────────────────────────
    language: str = "zh-CN"

    # ── Data directories ───────────────────────────────────────────────────
    data_dir: str = str(Path(__file__).resolve().parent / "data")

    @property
    def providers_path(self) -> Path:
        return Path(self.data_dir) / "providers.json"

    @property
    def templates_path(self) -> Path:
        return Path(self.data_dir) / "templates.json"

    @property
    def reports_dir(self) -> Path:
        return Path(self.data_dir) / "reports"

    def model_post_init(self, __context: Any) -> None:
        """Ensure data directories exist on first load."""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

# ── Helper: load/save JSON files -------------------------------------------

def load_json(path: Path) -> list[dict]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
