from __future__ import annotations

from typing import Any

import httpx
from pydantic.v1 import SecretStr

MODEL_RELAY_BASE_URL = "https://model-relay-api.zzengine.net"
MODEL_RELAY_API_KEY_VARIABLE = "MODEL_RELAY_API_KEY"  # pragma: allowlist secret


def resolve_api_key(value: Any, user_id: str | None = None) -> str:
    """Resolve a literal key or MODEL_RELAY_API_KEY env/global variable reference."""
    if isinstance(value, SecretStr):
        value = value.get_secret_value()
    api_key = str(value or "").strip()
    if not api_key:
        msg = "Model Relay API key is required."
        raise ValueError(msg)

    if api_key == MODEL_RELAY_API_KEY_VARIABLE:
        from lfx.base.models.unified_models import get_api_key_for_provider

        resolved = get_api_key_for_provider(user_id, "Model Relay", api_key)
        if resolved:
            return resolved
        msg = "MODEL_RELAY_API_KEY is not configured in Model providers or environment variables."
        raise ValueError(msg)

    return api_key


def post_task_submit(api_key: str, payload: dict[str, Any], *, timeout: float = 60.0) -> dict[str, Any]:
    response = httpx.post(
        f"{MODEL_RELAY_BASE_URL}/api/v1/task/submit",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        msg = "Model Relay returned a non-object response."
        raise TypeError(msg)
    return data


def get_task_query(api_key: str, task_uid: str, *, timeout: float = 30.0) -> dict[str, Any]:
    response = httpx.get(
        f"{MODEL_RELAY_BASE_URL}/api/v1/task/query",
        headers={"X-Api-Key": api_key},
        params={"task_uid": task_uid},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        msg = "Model Relay returned a non-object response."
        raise TypeError(msg)
    return data


def extract_text(value: Any) -> str | None:
    """Extract plain text from strings, Messages, or Data-like payloads."""
    if isinstance(value, str):
        return value.strip() or None

    text = getattr(value, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    data = getattr(value, "data", value)
    if not isinstance(data, dict):
        return None

    candidates = [
        data.get("text"),
        data.get("message"),
        data.get("prompt"),
        data.get("response"),
        data.get("data", {}).get("text") if isinstance(data.get("data"), dict) else None,
        data.get("data", {}).get("message") if isinstance(data.get("data"), dict) else None,
        data.get("data", {}).get("prompt") if isinstance(data.get("data"), dict) else None,
        data.get("data", {}).get("response") if isinstance(data.get("data"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def extract_task_uid(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None

    text = getattr(value, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    data = getattr(value, "data", value)
    if not isinstance(data, dict):
        return None

    candidates = [
        data.get("task_uid"),
        data.get("data", {}).get("task_uid") if isinstance(data.get("data"), dict) else None,
        data.get("data", {}).get("task", {}).get("task_uid") if isinstance(data.get("data"), dict) else None,
        data.get("task", {}).get("task_uid") if isinstance(data.get("task"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None
