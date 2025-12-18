import os
import re
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


def _safe_filename(name: str, *, fallback: str = "book") -> str:
    base = (name or "").strip() or fallback
    base = re.sub(r"[^a-zA-Z0-9 _\-]+", "", base).strip()
    base = re.sub(r"\s+", " ", base)
    return base[:120] or fallback


def export_book_to_pdf(book: dict, *, output_path: str | None = None) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF export requires 'reportlab'. Install it with: pip install reportlab"
        ) from exc

    title = str(book.get("title") or "Untitled")
    synopsis = str(book.get("synopsis") or "")

    if output_path is None:
        safe = _safe_filename(title)
        output_path = os.path.abspath(f"{safe}.pdf")

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=title,
        author="LivePrompt",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BookTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChapterTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceBefore=10,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            spaceAfter=8,
            firstLineIndent=0.6 * cm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Synopsis",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            spaceAfter=10,
        )
    )

    story: list = []

    story.append(Paragraph(title, styles["BookTitle"]))

    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(f"Generated: {created}", styles["Normal"]))
    story.append(Spacer(1, 12))

    if synopsis.strip():
        story.append(Paragraph("Synopsis", styles["Heading2"]))
        story.append(Paragraph(synopsis, styles["Synopsis"]))

    story.append(PageBreak())

    chapters = book.get("chapters")
    if not isinstance(chapters, list):
        chapters = []

    for idx, ch in enumerate(chapters, start=1):
        number = ch.get("number", idx)
        ch_title = str(ch.get("title") or f"Chapter {number}")
        story.append(Paragraph(f"Chapter {number}: {ch_title}", styles["ChapterTitle"]))

        paragraphs = ch.get("paragraphs")
        if not isinstance(paragraphs, list):
            paragraphs = []

        for p in paragraphs:
            text = str(p.get("text") or "").strip()
            if not text:
                continue
            story.append(Paragraph(text, styles["Body"]))

        if idx != len(chapters):
            story.append(PageBreak())

    def _on_page(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 2.2 * cm, 1.2 * cm, str(canvas.getPageNumber()))
        canvas.restoreState()

    logger.info("Writing PDF to %s", output_path)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return output_path
