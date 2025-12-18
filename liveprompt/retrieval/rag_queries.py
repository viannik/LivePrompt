from __future__ import annotations


def build_chapter_rag_queries(*, outline: dict, plan: dict, planned_chapter: dict) -> list[str]:
    queries: list[str] = []

    title = plan.get("title") if isinstance(plan, dict) else None
    synopsis = plan.get("synopsis") if isinstance(plan, dict) else None
    if isinstance(title, str) and title.strip():
        queries.append(title.strip())
    if isinstance(synopsis, str) and synopsis.strip():
        queries.append(synopsis.strip())

    ch_title = planned_chapter.get("title") if isinstance(planned_chapter, dict) else None
    ch_summary = planned_chapter.get("summary") if isinstance(planned_chapter, dict) else None
    if isinstance(ch_title, str) and ch_title.strip():
        queries.append(ch_title.strip())
    if isinstance(ch_summary, str) and ch_summary.strip():
        queries.append(ch_summary.strip())

    paragraphs = planned_chapter.get("paragraphs") if isinstance(planned_chapter, dict) else None
    if isinstance(paragraphs, list):
        for p in paragraphs:
            if not isinstance(p, dict):
                continue
            beat = p.get("beat")
            if isinstance(beat, str) and beat.strip():
                queries.append(beat.strip())

    chars = outline.get("characters") if isinstance(outline, dict) else None
    if isinstance(chars, list):
        names: list[str] = []
        for c in chars:
            if not isinstance(c, dict):
                continue
            nm = c.get("name")
            if isinstance(nm, str) and nm.strip():
                names.append(nm.strip())
        if names:
            queries.append("Characters: " + ", ".join(names[:12]))

    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        qn = " ".join((q or "").split()).strip()
        if not qn:
            continue
        if qn.lower() in seen:
            continue
        seen.add(qn.lower())
        out.append(qn)
    return out
