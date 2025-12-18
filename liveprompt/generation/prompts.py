from __future__ import annotations

import json


def outline_system_prompt() -> str:
    return (
        "You generate story planning output. "
        "Return ONLY valid JSON (no markdown, no prose). "
        "Use only standard double quotes and escape any internal quotes for JSON. "
        'Schema: {"main_plot": string, "characters": ['
        '{"name": string, "role": string, "motivation": string, "arc": string}]} '
        "Keep main_plot concise but complete (beginning, middle, end)."
    )


def outline_user_prompt(user_request: str) -> str:
    return (
        "User request: "
        f"{user_request}\n\n"
        "Generate the JSON object now."
    )


def plan_system_prompt() -> str:
    return (
        "You create a detailed book plan. "
        "Return ONLY valid JSON (no markdown, no prose). "
        "Use only standard double quotes and escape any internal quotes for JSON. "
        "Pacing rules: do NOT resolve the central mystery early. "
        "No public reveal, confession, arrest, or full wrap-up until the FINAL chapter. "
        "Each chapter must end with a new clue, reversal, or escalation, except the final chapter which resolves everything. "
        'Schema: {"title": string, "synopsis": string, "chapters": ['
        '{"number": integer, "title": string, "summary": string, "paragraphs": ['
        '{"number": integer, "beat": string}]}]}. '
        "Be consistent with the outline's plot and characters."
    )


def plan_user_prompt(outline: dict, *, chapters: int, paragraphs_per_chapter: int) -> str:
    outline_json = json.dumps(outline, ensure_ascii=False)
    return (
        "Create a chapter-by-chapter plan based on this outline JSON. "
        f"Chapters: {chapters}. Paragraphs per chapter: {paragraphs_per_chapter}.\n\n"
        f"Outline JSON: {outline_json}\n\n"
        "Return the plan JSON now."
    )


def chapter_system_prompt() -> str:
    return (
        "You are writing a novel chapter-by-chapter. "
        "You must follow the outline and the provided chapter plan. "
        "Ensure continuity with prior context and do not contradict character names, motivations, or timeline. "
        "Never repeat a scene that already happened in earlier chapters; always advance the story. "
        "If the prior context already contains a confrontation, confession, or public reveal, do NOT redo it. "
        "Do not introduce a new main culprit or change the culprit unless the plan explicitly says so. "
        "Do not introduce new named main characters unless they appear in the outline/plan; minor unnamed extras are ok. "
        "Protagonist agency rule: in every chapter the protagonist must take at least one decisive action to obtain evidence (stakeout, experiment, trap, verification, confrontation, etc.). "
        "Return ONLY valid JSON (no markdown, no prose). "
        "Use only standard double quotes and escape any internal quotes for JSON. "
        'Schema: {"number": integer, "title": string, "paragraphs": [{"number": integer, "text": string}]}. '
        "Return exactly one paragraph per planned beat and keep paragraph numbers identical to the plan. "
        "Each paragraph must be a real paragraph (multiple sentences), not a single short sentence."
    )


def chapter_user_prompt(
    *,
    outline: dict,
    plan: dict,
    planned_chapter: dict,
    retrieved_context: list[dict],
    recent_paragraphs: list[dict],
    total_chapters: int,
    min_words: int = 80,
    max_words: int = 140,
) -> str:
    chapter_number = planned_chapter.get("number")
    chapter_title = planned_chapter.get("title")
    chapter_summary = planned_chapter.get("summary")

    planned_paragraphs = planned_chapter.get("paragraphs")
    if not isinstance(planned_paragraphs, list):
        planned_paragraphs = []

    planned_numbers: list[int] = []
    for p in planned_paragraphs:
        if isinstance(p, dict) and isinstance(p.get("number"), int):
            planned_numbers.append(p["number"])

    is_final = False
    try:
        is_final = int(chapter_number) == int(total_chapters)
    except Exception:
        is_final = False

    recent_for_prompt: list[dict] = []
    if isinstance(recent_paragraphs, list):
        for item in recent_paragraphs[-6:]:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            recent_for_prompt.append(
                {
                    "chapter": item.get("chapter"),
                    "paragraph": item.get("paragraph"),
                    "text": text[:900],
                }
            )

    progress_rules = (
        f"This is chapter {chapter_number} of {total_chapters}. "
        + (
            "Because this is NOT the final chapter, you must NOT resolve the central mystery yet. "
            "Do NOT have a full public reveal, confession, arrest, or wrap-up. End with a new clue, reversal, or higher stakes."
            if not is_final
            else "Because this IS the final chapter, you must deliver the climax and resolution without repeating earlier scenes."
        )
    )

    return (
        "Write the full chapter as multiple paragraphs, aligned to the planned beats.\n\n"
        f"{progress_rules}\n\n"
        f"Paragraph length target: {min_words}-{max_words} words per paragraph (roughly). Each paragraph should have 3-6 sentences.\n"
        "Include concrete sensory detail and character action. Avoid summary-only paragraphs.\n\n"
        f"Most recent book text (do not repeat these events; build on them): {json.dumps(recent_for_prompt, ensure_ascii=False)}\n\n"
        f"Outline JSON: {json.dumps(outline, ensure_ascii=False)}\n\n"
        f"Plan JSON (high-level): {json.dumps(plan, ensure_ascii=False)}\n\n"
        f"Chapter number: {chapter_number}\n"
        f"Chapter title: {chapter_title}\n"
        f"Chapter summary: {chapter_summary}\n\n"
        f"Planned paragraphs (numbers + beats): {json.dumps(planned_paragraphs, ensure_ascii=False)}\n\n"
        f"Hard constraints: paragraphs array must contain exactly {len(planned_paragraphs)} items and must use exactly these paragraph numbers: {planned_numbers}. Do NOT return an empty list.\n\n"
        f"Relevant prior passages (vector search results): {json.dumps(retrieved_context, ensure_ascii=False)}\n\n"
        "Return the chapter JSON now."
    )
