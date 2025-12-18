from __future__ import annotations


class LivePromptError(Exception):
    """Base exception for this project."""


class ConfigError(LivePromptError):
    """Raised when required configuration is missing or invalid."""


class LLMError(LivePromptError):
    """Base exception for LLM-related failures."""


class LLMRequestError(LLMError):
    """Raised when an LLM request fails (network, provider error, etc.)."""


class LLMResponseError(LLMError):
    """Raised when the provider returns an unexpected response shape."""


class JSONParseError(LivePromptError):
    """Raised when model output cannot be parsed into valid JSON."""


class SchemaValidationError(LivePromptError):
    """Raised when parsed JSON doesn't match the expected schema."""
