from __future__ import annotations

import logging

from .chapter_writer import generate_chapter
from ..retrieval.rag_queries import build_chapter_rag_queries
from ..retrieval.retrieval import _hash_embedding, _retrieve_relevant_paragraphs
from ..core.exceptions import SchemaValidationError


logger = logging.getLogger(__name__)


def generate_book_from_plan(
    *,
    outline: dict,
    plan: dict,
    model: str,
    validate_book,
    validate_generated_chapter,
) -> dict:
    book = {
        "title": plan["title"],
        "synopsis": plan["synopsis"],
        "chapters": [],
    }

    paragraph_index: list[dict] = []

    total_chapters_effective = (
        len(plan.get("chapters", [])) if isinstance(plan.get("chapters"), list) else 0
    )
    if total_chapters_effective <= 0:
        raise SchemaValidationError("Plan did not contain chapters")

    for ch in plan["chapters"]:
        chapter_number = ch["number"]
        logger.info("Starting chapter %d/%d", chapter_number, len(plan["chapters"]))

        rag_queries = build_chapter_rag_queries(outline=outline, plan=plan, planned_chapter=ch)
        retrieved = _retrieve_relevant_paragraphs(
            paragraph_index=paragraph_index,
            queries=rag_queries,
            current_chapter=chapter_number,
            top_k=10,
        )

        recent = []
        if paragraph_index:
            recent = paragraph_index[-8:]

        chapter = generate_chapter(
            outline=outline,
            plan=plan,
            planned_chapter=ch,
            retrieved_context=retrieved,
            recent_paragraphs=recent,
            total_chapters=total_chapters_effective,
            model=model,
            validate_generated_chapter=validate_generated_chapter,
        )

        for paragraph in chapter.get("paragraphs", []):
            paragraph_index.append(
                {
                    "chapter": chapter_number,
                    "paragraph": paragraph.get("number"),
                    "text": paragraph.get("text"),
                    "_vec": _hash_embedding(paragraph.get("text", "")),
                }
            )

        book["chapters"].append(chapter)

    validate_book(book)
    return book
