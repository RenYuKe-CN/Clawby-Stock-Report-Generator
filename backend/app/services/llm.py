"""Unified LLM client that routes requests to the configured provider.

Supported types:
  - openai / custom_openai  →  OpenAI Chat Completions API
  - anthropic / custom_anthropic  →  Anthropic Messages API
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from app.config import load_json, settings, save_json
from app.models.schemas import LLMProviderResponse, ProviderType


# ── Provider registry (in-memory, backed by providers.json) ─────────────────

class ProviderRegistry:
    """Manages LLM provider configurations."""

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}
        self._default_id: str | None = None
        self._load()

    # ── Loading / saving ────────────────────────────────────────────────

    def _load(self) -> None:
        raw = load_json(settings.providers_path)

        # Import the .env default provider on first run
        if not raw and settings.llm_api_key:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            default: dict[str, Any] = {
                "id": "prov_default",
                "name": f"默认 {settings.llm_provider_type}",
                "provider_type": settings.llm_provider_type,
                "api_base": settings.llm_api_base,
                "api_key": settings.llm_api_key,
                "default_model": settings.llm_model,
                "supported_models": [settings.llm_model],
                "max_tokens": 8192,
                "supports_streaming": True,
                "is_default": True,
                "is_available": False,
                "last_tested_at": None,
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
            self._providers[default["id"]] = default
            self._default_id = default["id"]
            self._persist()
            return

        for p in raw:
            pid = p["id"]
            self._providers[pid] = p
            if p.get("is_default"):
                self._default_id = pid

    def _persist(self) -> None:
        save_json(settings.providers_path, list(self._providers.values()))

    # ── CRUD ────────────────────────────────────────────────────────────

    def list(self) -> list[dict[str, Any]]:
        return list(self._providers.values())

    def get(self, pid: str) -> dict[str, Any] | None:
        return self._providers.get(pid)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        from datetime import datetime, timezone
        import uuid
        pid = f"prov_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        entry: dict[str, Any] = {
            "id": pid,
            "name": data["name"],
            "provider_type": data["provider_type"],
            "api_base": data["api_base"],
            "api_key": data.get("api_key", ""),
            "default_model": data["default_model"],
            "supported_models": data.get("supported_models", [data["default_model"]]),
            "max_tokens": data.get("max_tokens", 8192),
            "supports_streaming": data.get("supports_streaming", True),
            "is_default": len(self._providers) == 0,
            "is_available": False,
            "last_tested_at": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        self._providers[pid] = entry
        if entry["is_default"]:
            self._default_id = pid
        self._persist()
        return entry

    def update(self, pid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        entry = self._providers.get(pid)
        if not entry:
            return None
        from datetime import datetime, timezone
        for key in ("name", "api_base", "api_key", "default_model",
                     "supported_models", "max_tokens", "supports_streaming"):
            if key in data and data[key] is not None:
                entry[key] = data[key]
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._persist()
        return entry

    def delete(self, pid: str) -> bool:
        if pid not in self._providers:
            return False
        was_default = self._providers[pid].get("is_default", False)
        del self._providers[pid]
        if was_default and self._providers:
            # Assign next available as default
            first_id = next(iter(self._providers))
            self._providers[first_id]["is_default"] = True
            self._default_id = first_id
        elif was_default:
            self._default_id = None
        self._persist()
        return True

    def set_default(self, pid: str) -> bool:
        if pid not in self._providers:
            return False
        for p in self._providers.values():
            p["is_default"] = False
        self._providers[pid]["is_default"] = True
        self._default_id = pid
        self._persist()
        return True

    @property
    def default_id(self) -> str | None:
        return self._default_id


# Singleton
registry = ProviderRegistry()


# ── Connectivity test ───────────────────────────────────────────────────────

async def test_provider(pid: str) -> dict[str, Any]:
    """Test a provider by sending a minimal chat completion request."""
    entry = registry.get(pid)
    if not entry:
        return {"success": False, "message": "Provider not found", "latency_ms": None}

    ptype: ProviderType = entry["provider_type"]
    api_base = entry["api_base"].rstrip("/")
    api_key = entry["api_key"]
    model = entry["default_model"]

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if ptype in ("openai", "custom_openai"):
                resp = await client.post(
                    f"{api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Say OK"}],
                        "max_tokens": 10,
                    },
                )
                resp.raise_for_status()
                latency = int((time.monotonic() - start) * 1000)
                return {"success": True, "message": "Connected", "latency_ms": latency}

            elif ptype in ("anthropic", "custom_anthropic"):
                resp = await client.post(
                    f"{api_base}/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Say OK"}],
                    },
                )
                resp.raise_for_status()
                latency = int((time.monotonic() - start) * 1000)
                return {"success": True, "message": "Connected", "latency_ms": latency}

            return {"success": False, "message": f"Unknown provider type: {ptype}", "latency_ms": None}

    except httpx.HTTPStatusError as exc:
        latency = int((time.monotonic() - start) * 1000)
        return {"success": False, "message": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}", "latency_ms": latency}
    except httpx.TimeoutException:
        return {"success": False, "message": "Connection timed out (15s)", "latency_ms": None}
    except Exception as exc:
        latency = int((time.monotonic() - start) * 1000)
        return {"success": False, "message": str(exc), "latency_ms": latency}


async def update_provider_status(pid: str, result: dict[str, Any]) -> None:
    """Update provider availability after a test."""
    entry = registry.get(pid)
    if not entry:
        return
    from datetime import datetime, timezone
    entry["is_available"] = result["success"]
    entry["last_tested_at"] = datetime.now(timezone.utc).isoformat()
    entry["error_message"] = None if result["success"] else result["message"]
    registry._persist()


# ── Streaming generation ────────────────────────────────────────────────────

async def generate_stream(
    provider_id: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> AsyncIterator[tuple[str, str]]:
    """Yield (event_type, data_string) pairs for SSE streaming.

    event_type is one of: "chunk", "error"
    """
    entry = registry.get(provider_id)
    if not entry:
        yield "error", json.dumps({"code": "provider_not_found", "message": f"Provider {provider_id} not found"})
        return

    ptype: ProviderType = entry["provider_type"]
    api_base = entry["api_base"].rstrip("/")
    api_key = entry["api_key"]

    async with httpx.AsyncClient(timeout=25.0) as client:
        try:
            if ptype in ("openai", "custom_openai"):
                async with client.stream(
                    "POST",
                    f"{api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": True,
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload == "[DONE]":
                            break
                        try:
                            obj = json.loads(payload)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield "chunk", json.dumps({"text": content})
                        except json.JSONDecodeError:
                            continue

            elif ptype in ("anthropic", "custom_anthropic"):
                async with client.stream(
                    "POST",
                    f"{api_base}/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 8192,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                        "stream": True,
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        try:
                            obj = json.loads(payload)
                            if obj.get("type") == "content_block_delta":
                                    delta = obj.get("delta", {})
                                    text = delta.get("text", "")
                                    if text:
                                        yield "chunk", json.dumps({"text": text})
                        except json.JSONDecodeError:
                            continue

            else:
                yield "error", json.dumps({"code": "unsupported_type", "message": f"Unsupported provider type: {ptype}"})

        except httpx.HTTPStatusError as exc:
            yield "error", json.dumps({
                "code": "http_error",
                "message": f"LLM API returned {exc.response.status_code}: {exc.response.text[:300]}",
            })
        except Exception as exc:
            yield "error", json.dumps({
                "code": "stream_error",
                "message": str(exc),
            })
