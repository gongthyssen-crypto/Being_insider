from __future__ import annotations

import os
from threading import Lock

from app.schemas import RuntimeSettings, RuntimeSettingsUpdate

_SETTINGS_LOCK = Lock()


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def _normalize_settings(settings: RuntimeSettings) -> RuntimeSettings:
    return RuntimeSettings(
        deepseek_base_url=settings.deepseek_base_url.strip().rstrip("/"),
        deepseek_api_key=settings.deepseek_api_key.strip(),
        deepseek_model=settings.deepseek_model.strip(),
        deepseek_max_tokens=_clamp_int(
            settings.deepseek_max_tokens,
            minimum=512,
            maximum=8192,
        ),
        deepseek_thinking_enabled=bool(settings.deepseek_thinking_enabled),
        turn_knowledge_max_matches=_clamp_int(
            settings.turn_knowledge_max_matches,
            minimum=1,
            maximum=8,
        ),
        turn_knowledge_max_excerpt_chars=_clamp_int(
            settings.turn_knowledge_max_excerpt_chars,
            minimum=160,
            maximum=2400,
        ),
    )


_runtime_settings = _normalize_settings(
    RuntimeSettings(
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        deepseek_max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "4096")),
        deepseek_thinking_enabled=_env_flag("DEEPSEEK_THINKING_ENABLED", True),
        turn_knowledge_max_matches=int(os.getenv("TURN_KNOWLEDGE_MAX_MATCHES", "4")),
        turn_knowledge_max_excerpt_chars=int(
            os.getenv("TURN_KNOWLEDGE_MAX_EXCERPT_CHARS", "720")
        ),
    )
)


def get_runtime_settings() -> RuntimeSettings:
    with _SETTINGS_LOCK:
        return _runtime_settings.model_copy(deep=True)


def update_runtime_settings(payload: RuntimeSettingsUpdate) -> RuntimeSettings:
    global _runtime_settings

    with _SETTINGS_LOCK:
        merged = _runtime_settings.model_dump()
        for key, value in payload.model_dump(exclude_none=True).items():
            merged[key] = value
        _runtime_settings = _normalize_settings(RuntimeSettings(**merged))
        return _runtime_settings.model_copy(deep=True)
