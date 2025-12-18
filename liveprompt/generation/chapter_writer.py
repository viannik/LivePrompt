from __future__ import annotations

import logging

from ..llm.json import get_json_object
from .prompts import chapter_system_prompt, chapter_user_prompt


logger = logging.getLogger(__name__)


def generate_chapter(
    *,
    outline: dict,
    plan: dict,
    planned_chapter: dict,
    retrieved_context: list[dict],
    recent_paragraphs: list[dict],
    total_chapters: int,
    model: str,
    validate_generated_chapter,
) -> dict:
    max_attempts = 2

    system_prompt = chapter_system_prompt()
    base_prompt = chapter_user_prompt(
        outline=outline,
        plan=plan,
        planned_chapter=planned_chapter,
        retrieved_context=retrieved_context,
        recent_paragraphs=recent_paragraphs,
        total_chapters=total_chapters,
    )

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        attempt_temperature = 0.7 if attempt == 1 else 0.4
        attempt_prompt = base_prompt
        if last_exc is not None:
            attempt_prompt = (
                base_prompt
                + "\n\n"
                + f"Previous attempt failed validation with error: {type(last_exc).__name__}: {last_exc}. "
                + "Regenerate the chapter JSON from scratch and satisfy all constraints exactly."
            )

        data = get_json_object(
            prompt=attempt_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=attempt_temperature,
            schema_hint='{"number": integer, "title": string, "paragraphs": [{"number": integer, "text": string}]}',
            default_max_tokens=5200,
        )

        if isinstance(data, dict):
            generated_title = data.get("title")
            if not isinstance(generated_title, str) or not generated_title.strip():
                fallback_title = planned_chapter.get("title")
                if isinstance(fallback_title, str) and fallback_title.strip():
                    data["title"] = fallback_title.strip()

        try:
            validate_generated_chapter(data)
            return data
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Generated chapter failed validation ch=%s attempt=%d/%d error=%s",
                planned_chapter.get("number"),
                attempt,
                max_attempts,
                str(exc),
            )

    assert last_exc is not None
    raise last_exc
