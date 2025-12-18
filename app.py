import os
import sys
import json
import logging

from liveprompt.generation.service import (
    generate_book_plot_and_characters,
    generate_book_from_outline,
)


def configure_logging() -> None:
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main() -> None:
    configure_logging()
    try:
        outline = generate_book_plot_and_characters(
            "A cozy mystery set in a small coastal town where a baker solves crimes.",
        )
        book = generate_book_from_outline(outline, chapters=4)

        try:
            from liveprompt.export.pdf_export import export_book_to_pdf

            pdf_path = export_book_to_pdf(
                book,
                output_path=os.getenv("BOOK_PDF_PATH") or None,
            )
            logging.info("Saved PDF: %s", pdf_path)
        except Exception as exc:
            logging.warning("PDF export skipped: %s", exc)

        print(json.dumps(book, indent=2, ensure_ascii=False))
    except Exception as exc:
        logging.exception("Error during book generation")
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


