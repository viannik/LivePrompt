from __future__ import annotations

import logging

from .client import get_completion
from ..core.validation import _extract_json_object


logger = logging.getLogger(__name__)


def get_json_object(
    *,
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    schema_hint: str,
    default_max_tokens: int | None = None,
) -> dict:
    """Call the LLM and return a parsed JSON object."""

    max_tokens = default_max_tokens

    raw_kwargs = {
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    if max_tokens is not None:
        raw_kwargs["max_completion_tokens"] = max_tokens

    raw = get_completion(prompt, model=model, system_prompt=system_prompt, **raw_kwargs)
    try:
        return _extract_json_object(raw)
    except Exception as first_exc:
        logger.warning(
            "Model returned invalid JSON; attempting single retry error=%s",
            type(first_exc).__name__,
        )

        repair_system = (
            "You are a JSON repair tool. "
            "You will be given invalid JSON that should represent a single JSON object. "
            "Return ONLY the corrected JSON object. "
            "Do not add commentary, code fences, or extra text."
        )
        repair_prompt = (
            f"Target schema: {schema_hint}\n\n"
            "Fix the following invalid JSON so it becomes strictly valid JSON. "
            "Do not change meaning; only fix syntax (missing commas, quoting, escaping, etc.).\n\n"
            f"INVALID_JSON_START\n{raw}\nINVALID_JSON_END"
        )
        try:
            repaired_raw = get_completion(
                repair_prompt,
                model=model,
                system_prompt=repair_system,
                temperature=0.0,
                max_completion_tokens=max_tokens,
            )
            return _extract_json_object(repaired_raw)
        except Exception as exc:
            logger.warning("JSON repair failed: %s", type(exc).__name__)

        retry_system = (
            "You output strictly valid JSON only. "
            "No markdown, no explanations, no trailing text. "
            "All strings must use double quotes and must be properly escaped for JSON."
        )
        retry_prompt = (
            f"Target schema: {schema_hint}\n\n"
            "Your previous output was invalid JSON. "
            "Re-generate the JSON from scratch for the original task below. Output ONLY JSON.\n\n"
            f"ORIGINAL_SYSTEM_PROMPT:\n{system_prompt}\n\n"
            f"ORIGINAL_USER_PROMPT:\n{prompt}"
        )

        try:
            retry_raw = get_completion(
                retry_prompt,
                model=model,
                system_prompt=retry_system,
                temperature=0.0,
                max_completion_tokens=max_tokens,
            )
            try:
                return _extract_json_object(retry_raw)
            except Exception:
                repair_prompt_2 = (
                    f"Target schema: {schema_hint}\n\n"
                    "Fix the following invalid JSON so it becomes strictly valid JSON. "
                    "Return ONLY the corrected JSON object.\n\n"
                    f"INVALID_JSON_START\n{retry_raw}\nINVALID_JSON_END"
                )
                repaired_retry_raw = get_completion(
                    repair_prompt_2,
                    model=model,
                    system_prompt=repair_system,
                    temperature=0.0,
                    max_completion_tokens=max_tokens,
                )
                return _extract_json_object(repaired_retry_raw)
        except Exception as exc:
            logger.warning("JSON retry failed: %s", type(exc).__name__)
            raise first_exc
