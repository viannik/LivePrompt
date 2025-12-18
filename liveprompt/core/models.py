from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .exceptions import SchemaValidationError


def _require_mapping(value: Any, *, ctx: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"Expected object for {ctx}")
    return value


def _require_str(obj: Mapping[str, Any], key: str, *, ctx: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{ctx} '{key}' must be a non-empty string")
    return value.strip()


def _require_int(obj: Mapping[str, Any], key: str, *, ctx: str) -> int:
    value = obj.get(key)
    if not isinstance(value, int):
        raise SchemaValidationError(f"{ctx} '{key}' must be an integer")
    return value


def _require_list(obj: Mapping[str, Any], key: str, *, ctx: str) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list) or not value:
        raise SchemaValidationError(f"{ctx} '{key}' must be a non-empty list")
    return value


@dataclass(frozen=True)
class Character:
    name: str
    role: str
    motivation: str
    arc: str

    @classmethod
    def from_dict(cls, data: Any) -> Character:
        obj = _require_mapping(data, ctx="character")
        return cls(
            name=_require_str(obj, "name", ctx="character"),
            role=_require_str(obj, "role", ctx="character"),
            motivation=_require_str(obj, "motivation", ctx="character"),
            arc=_require_str(obj, "arc", ctx="character"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "motivation": self.motivation,
            "arc": self.arc,
        }


@dataclass(frozen=True)
class Outline:
    main_plot: str
    characters: list[Character]

    @classmethod
    def from_dict(cls, data: Any) -> Outline:
        obj = _require_mapping(data, ctx="outline")
        main_plot = _require_str(obj, "main_plot", ctx="outline")
        characters_raw = _require_list(obj, "characters", ctx="outline")
        characters = [Character.from_dict(c) for c in characters_raw]
        return cls(main_plot=main_plot, characters=characters)

    def to_dict(self) -> dict[str, Any]:
        return {
            "main_plot": self.main_plot,
            "characters": [c.to_dict() for c in self.characters],
        }


@dataclass(frozen=True)
class PlannedParagraph:
    number: int
    beat: str

    @classmethod
    def from_dict(cls, data: Any) -> PlannedParagraph:
        obj = _require_mapping(data, ctx="planned paragraph")
        return cls(
            number=_require_int(obj, "number", ctx="planned paragraph"),
            beat=_require_str(obj, "beat", ctx="planned paragraph"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"number": self.number, "beat": self.beat}


@dataclass(frozen=True)
class PlannedChapter:
    number: int
    title: str
    summary: str
    paragraphs: list[PlannedParagraph]

    @classmethod
    def from_dict(cls, data: Any) -> PlannedChapter:
        obj = _require_mapping(data, ctx="planned chapter")
        paragraphs_raw = _require_list(obj, "paragraphs", ctx="planned chapter")
        paragraphs = [PlannedParagraph.from_dict(p) for p in paragraphs_raw]
        return cls(
            number=_require_int(obj, "number", ctx="planned chapter"),
            title=_require_str(obj, "title", ctx="planned chapter"),
            summary=_require_str(obj, "summary", ctx="planned chapter"),
            paragraphs=paragraphs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "summary": self.summary,
            "paragraphs": [p.to_dict() for p in self.paragraphs],
        }


@dataclass(frozen=True)
class BookPlan:
    title: str
    synopsis: str
    chapters: list[PlannedChapter]

    @classmethod
    def from_dict(cls, data: Any) -> BookPlan:
        obj = _require_mapping(data, ctx="plan")
        chapters_raw = _require_list(obj, "chapters", ctx="plan")
        chapters = [PlannedChapter.from_dict(ch) for ch in chapters_raw]
        return cls(
            title=_require_str(obj, "title", ctx="plan"),
            synopsis=_require_str(obj, "synopsis", ctx="plan"),
            chapters=chapters,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "synopsis": self.synopsis,
            "chapters": [c.to_dict() for c in self.chapters],
        }


@dataclass(frozen=True)
class Paragraph:
    number: int
    text: str

    @classmethod
    def from_dict(cls, data: Any) -> Paragraph:
        obj = _require_mapping(data, ctx="paragraph")
        return cls(
            number=_require_int(obj, "number", ctx="paragraph"),
            text=_require_str(obj, "text", ctx="paragraph"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"number": self.number, "text": self.text}


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    paragraphs: list[Paragraph]

    @classmethod
    def from_dict(cls, data: Any) -> Chapter:
        obj = _require_mapping(data, ctx="chapter")
        paragraphs_raw = _require_list(obj, "paragraphs", ctx="chapter")
        paragraphs = [Paragraph.from_dict(p) for p in paragraphs_raw]
        return cls(
            number=_require_int(obj, "number", ctx="chapter"),
            title=_require_str(obj, "title", ctx="chapter"),
            paragraphs=paragraphs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "paragraphs": [p.to_dict() for p in self.paragraphs],
        }


@dataclass(frozen=True)
class Book:
    title: str
    synopsis: str
    chapters: list[Chapter]

    @classmethod
    def from_dict(cls, data: Any) -> Book:
        obj = _require_mapping(data, ctx="book")
        chapters_raw = _require_list(obj, "chapters", ctx="book")
        chapters = [Chapter.from_dict(ch) for ch in chapters_raw]
        return cls(
            title=_require_str(obj, "title", ctx="book"),
            synopsis=_require_str(obj, "synopsis", ctx="book"),
            chapters=chapters,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "synopsis": self.synopsis,
            "chapters": [c.to_dict() for c in self.chapters],
        }
