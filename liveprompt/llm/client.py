import time
import random
import logging
from openai import OpenAI

from ..core.exceptions import ConfigError, LLMRequestError, LLMResponseError
from ..core.settings import OpenAISettings


logger = logging.getLogger(__name__)

_openai_client: OpenAI | None = None
_openai_settings: OpenAISettings | None = None


def _sleep_with_backoff(
    *,
    attempt: int,
    retry_after_s: float | None = None,
    base_seconds: float,
    max_seconds: float,
) -> None:
    if retry_after_s is not None and retry_after_s > 0:
        delay_s = float(retry_after_s)
    else:
        delay_s = min(max_seconds, base_seconds * (2 ** max(0, attempt - 1)))
        delay_s = delay_s * (0.8 + 0.4 * random.random())

    logger.warning("Rate limited (429). Sleeping %.2fs before retry.", delay_s)
    time.sleep(delay_s)


def get_completion(
    prompt: str,
    *,
    model: str = "gpt-4o-mini",
    system_prompt: str | None = None,
    **kwargs,
) -> str:
    global _openai_client
    global _openai_settings

    if _openai_settings is None:
        _openai_settings = OpenAISettings.from_env()

    if _openai_client is None:
        _openai_client = OpenAI(api_key=_openai_settings.api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    start = time.perf_counter()
    if "max_completion_tokens" in kwargs and "max_tokens" not in kwargs:
        kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")

    allowed_keys = {
        "temperature",
        "top_p",
        "max_tokens",
        "stop",
        "stream",
        "response_format",
    }
    extra_keys = sorted([k for k in kwargs.keys() if k not in allowed_keys])
    if extra_keys:
        logger.debug("Ignoring unsupported args for OpenAI: %s", extra_keys)
        for k in extra_keys:
            kwargs.pop(k, None)

    # Do not pass None-valued fields to the SDK.
    for k in list(kwargs.keys()):
        if kwargs.get(k) is None:
            kwargs.pop(k, None)

    if "stream" not in kwargs:
        kwargs["stream"] = False

    logger.debug(
        "OpenAI request start model=%s prompt_chars=%d system_prompt=%s args=%s",
        model,
        len(prompt or ""),
        bool(system_prompt),
        {k: kwargs.get(k) for k in sorted(kwargs.keys())},
    )

    max_retries = _openai_settings.max_retries
    attempt = 0
    while True:
        attempt += 1
        try:
            completion = _openai_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            break
        except ConfigError:
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            retry_after = None
            if getattr(exc, "response", None) is not None:
                try:
                    retry_after = exc.response.headers.get("retry-after")
                except Exception:
                    retry_after = None

            if status_code == 429 and attempt <= max_retries:
                retry_after_s = None
                if retry_after is not None:
                    try:
                        retry_after_s = float(retry_after)
                    except ValueError:
                        retry_after_s = None
                logger.warning(
                    "OpenAI request rate limited after %.1fms (attempt %d/%d).",
                    elapsed_ms,
                    attempt,
                    max_retries,
                )
                _sleep_with_backoff(
                    attempt=attempt,
                    retry_after_s=retry_after_s,
                    base_seconds=_openai_settings.backoff_base_seconds,
                    max_seconds=_openai_settings.backoff_max_seconds,
                )
                continue

            logger.exception("OpenAI request failed after %.1fms", elapsed_ms)
            raise LLMRequestError(str(exc)) from exc

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.debug("OpenAI request done elapsed_ms=%.1f", elapsed_ms)

    if kwargs.get("stream"):
        chunks: list[str] = []
        for chunk in completion:
            try:
                delta = chunk.choices[0].delta.content
            except Exception:
                delta = None
            if delta:
                chunks.append(delta)
        return "".join(chunks)

    try:
        return completion.choices[0].message.content
    except (KeyError, IndexError, AttributeError) as exc:
        raise LLMResponseError(f"Unexpected response: {completion}") from exc


