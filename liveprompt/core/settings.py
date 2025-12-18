from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .exceptions import ConfigError


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    max_retries: int = 3
    backoff_base_seconds: float = 1.5
    backoff_max_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "OpenAISettings":
        load_dotenv()
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise ConfigError("OPENAI_API_KEY not found in environment")

        def _int(name: str, default: int) -> int:
            raw = os.getenv(name)
            if raw is None or not raw.strip():
                return default
            try:
                return int(raw)
            except ValueError as exc:
                raise ConfigError(f"Invalid {name}: {raw!r}") from exc

        def _float(name: str, default: float) -> float:
            raw = os.getenv(name)
            if raw is None or not raw.strip():
                return default
            try:
                return float(raw)
            except ValueError as exc:
                raise ConfigError(f"Invalid {name}: {raw!r}") from exc

        return cls(
            api_key=api_key,
            max_retries=_int("OPENAI_MAX_RETRIES", 3),
            backoff_base_seconds=_float(
                "OPENAI_BACKOFF_BASE_SECONDS",
                1.5,
            ),
            backoff_max_seconds=_float(
                "OPENAI_BACKOFF_MAX_SECONDS",
                60.0,
            ),
        )


@dataclass(frozen=True)
class GenerationSettings:
    model: str = "gpt-4o-mini"
    plan_chapters: int = 8
    paragraphs_per_chapter: int = 6

    @classmethod
    def from_env(cls) -> "GenerationSettings":
        model = (os.getenv("BOOK_MODEL") or cls.model).strip() or cls.model

        def _int(name: str, default: int) -> int:
            raw = os.getenv(name)
            if raw is None or not raw.strip():
                return default
            try:
                return int(raw)
            except ValueError as exc:
                raise ConfigError(f"Invalid {name}: {raw!r}") from exc

        return cls(
            model=model,
            plan_chapters=_int("BOOK_CHAPTERS", cls.plan_chapters),
            paragraphs_per_chapter=_int("BOOK_PARAGRAPHS_PER_CHAPTER", cls.paragraphs_per_chapter),
        )
