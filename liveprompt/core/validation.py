import json
import logging

from .exceptions import JSONParseError, SchemaValidationError
from .models import Book, BookPlan, Chapter, Outline

logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise JSONParseError("Model output did not contain a JSON object")

    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise JSONParseError(str(exc)) from exc


def _validate_outline(data: dict) -> None:
    try:
        Outline.from_dict(data)
    except SchemaValidationError:
        raise
    except Exception as exc:
        raise SchemaValidationError(str(exc)) from exc


def _validate_book(data: dict) -> None:
    try:
        Book.from_dict(data)
    except SchemaValidationError:
        raise
    except Exception as exc:
        raise SchemaValidationError(str(exc)) from exc


def _validate_generated_chapter(chapter: dict) -> None:
    try:
        Chapter.from_dict(chapter)
    except SchemaValidationError:
        raise
    except Exception as exc:
        raise SchemaValidationError(str(exc)) from exc


def _validate_book_plan(data: dict) -> None:
    try:
        BookPlan.from_dict(data)
    except SchemaValidationError:
        raise
    except Exception as exc:
        raise SchemaValidationError(str(exc)) from exc


