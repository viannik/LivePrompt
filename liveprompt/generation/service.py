import logging

from .pipeline import generate_book_from_plan
from ..llm.json import get_json_object
from ..core.models import Book, BookPlan, Outline
from .prompts import (
    outline_system_prompt,
    outline_user_prompt,
    plan_system_prompt,
    plan_user_prompt,
)
from ..core.settings import GenerationSettings
from ..core.validation import (
    _validate_book,
    _validate_book_plan,
    _validate_generated_chapter,
    _validate_outline,
)


logger = logging.getLogger(__name__)



class BookGenerator:
    def __init__(self, *, settings: GenerationSettings | None = None, model: str | None = None) -> None:
        self._settings = settings or GenerationSettings.from_env()
        self._model = (model or self._settings.model).strip() or self._settings.model

    @property
    def model(self) -> str:
        return self._model

    def generate_outline(self, user_request: str) -> Outline:
        data = generate_book_plot_and_characters(user_request, model=self.model)
        return Outline.from_dict(data)

    def generate_plan(
        self,
        outline: Outline,
        *,
        chapters: int | None = None,
        paragraphs_per_chapter: int | None = None,
    ) -> BookPlan:
        data = generate_book_plan_from_outline(
            outline.to_dict(),
            model=self.model,
            chapters=chapters if chapters is not None else self._settings.plan_chapters,
            paragraphs_per_chapter=(
                paragraphs_per_chapter
                if paragraphs_per_chapter is not None
                else self._settings.paragraphs_per_chapter
            ),
        )
        return BookPlan.from_dict(data)

    def generate_book(
        self,
        outline: Outline,
        *,
        chapters: int | None = None,
        paragraphs_per_chapter: int | None = None,
    ) -> Book:
        book_dict = generate_book_from_outline(
            outline.to_dict(),
            model=self.model,
            chapters=chapters if chapters is not None else self._settings.plan_chapters,
            paragraphs_per_chapter=(
                paragraphs_per_chapter
                if paragraphs_per_chapter is not None
                else self._settings.paragraphs_per_chapter
            ),
        )
        return Book.from_dict(book_dict)



def generate_book_plot_and_characters(
    user_request: str, *, model: str = "gpt-4o-mini"
) -> dict:
    logger.info("Generating outline model=%s", model)
    data = get_json_object(
        prompt=outline_user_prompt(user_request),
        system_prompt=outline_system_prompt(),
        model=model,
        temperature=0.4,
        schema_hint='{"main_plot": string, "characters": [{"name": string, "role": string, "motivation": string, "arc": string}]}',
        default_max_tokens=1200,
    )
    _validate_outline(data)
    return data


def generate_book_plan_from_outline(
    outline: dict,
    *,
    model: str = "gpt-4o-mini",
    chapters: int = 8,
    paragraphs_per_chapter: int = 6,
) -> dict:
    logger.info("Generating book plan chapters=%d", chapters)
    Outline.from_dict(outline)
    plan = get_json_object(
        prompt=plan_user_prompt(outline, chapters=chapters, paragraphs_per_chapter=paragraphs_per_chapter),
        system_prompt=plan_system_prompt(),
        model=model,
        temperature=0.0,
        schema_hint=(
            '{"title": string, "synopsis": string, "chapters": '
            '[{"number": integer, "title": string, "summary": string, "paragraphs": '
            '[{"number": integer, "beat": string}]}]}'
        ),
        default_max_tokens=3500,
    )
    _validate_book_plan(plan)
    return plan


def generate_book_from_outline(
    outline: dict,
    *,
    model: str = "gpt-4o-mini",
    chapters: int = 8,
    paragraphs_per_chapter: int = 6,
) -> dict:
    outline_model = Outline.from_dict(outline)
    plan = generate_book_plan_from_outline(
        outline_model.to_dict(),
        model=model,
        chapters=chapters,
        paragraphs_per_chapter=paragraphs_per_chapter,
    )
    book = generate_book_from_plan(
        outline=outline_model.to_dict(),
        plan=plan,
        model=model,
        validate_book=_validate_book,
        validate_generated_chapter=_validate_generated_chapter,
    )
    return book


