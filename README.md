# LivePrompt

LivePrompt is a small Python project that generates a complete short book from a single prompt.
It uses OpenAI chat completions to:

- produce an **outline** (main plot + characters)
- expand the outline into a **chapter plan** (chapter summaries + paragraph beats)
- write each **chapter** as paragraphs aligned to the plan

Outputs are returned as structured JSON and can optionally be exported to PDF.

## How it works

The high-level pipeline is:

1. **Outline**: `generate_book_plot_and_characters()`
2. **Plan**: `generate_book_plan_from_outline()`
3. **Chapters**: `generate_book_from_plan()` iterates through chapters and calls the chapter writer

The model is instructed to return **JSON only** (no markdown / no extra prose). If the model returns invalid JSON, the project performs a **single repair + retry strategy** and then validates the result against the expected schema.

For continuity, the chapter pipeline keeps an in-memory index of previously generated paragraphs and uses a lightweight retrieval step to surface relevant prior passages for each new chapter.

## Project layout

- `app.py`
  - Example entry point that runs the full pipeline and prints the final JSON
  - Optionally exports to PDF
- `liveprompt/generation/`
  - Orchestrates outline/plan/chapter generation and contains the prompt templates
- `liveprompt/llm/`
  - OpenAI client wrapper and JSON parsing/repair logic
- `liveprompt/core/`
  - Typed models, settings, and schema/validation errors
- `liveprompt/retrieval/`
  - Lightweight retrieval utilities used to keep chapter-to-chapter consistency
- `liveprompt/export/pdf_export.py`
  - Optional PDF export via `reportlab`

## Output format

The generated book is a JSON object with this shape:

```json
{
  "title": "...",
  "synopsis": "...",
  "chapters": [
    {
      "number": 1,
      "title": "...",
      "paragraphs": [
        {"number": 1, "text": "..."}
      ]
    }
  ]
}
```

## Requirements

- Python 3.10+

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root (this repo ignores it) and add:

```bash
OPENAI_API_KEY=your_api_key_here
```

## Run

```bash
python app.py
```

`app.py` currently uses a hardcoded example prompt. Change the prompt string in `app.py` to generate a different book.

## PDF export (optional)

If `reportlab` is installed (it is included in `requirements.txt`), the script will attempt to write a PDF.

Set an explicit output path if desired:

```bash
BOOK_PDF_PATH=./output/my_book.pdf
```

## Configuration

Environment variables:

- `OPENAI_API_KEY` (required)
- `BOOK_MODEL` (optional, default: `gpt-4o-mini`)
- `BOOK_CHAPTERS` (optional, default: `8`)
- `BOOK_PARAGRAPHS_PER_CHAPTER` (optional, default: `6`)
- `OPENAI_MAX_RETRIES` (optional, default: `3`)
- `OPENAI_BACKOFF_BASE_SECONDS` (optional, default: `1.5`)
- `OPENAI_BACKOFF_MAX_SECONDS` (optional, default: `60.0`)
- `LOG_LEVEL` (optional, e.g. `INFO`, `DEBUG`)
- `BOOK_PDF_PATH` (optional)

## Notes

- Your OpenAI API key should **never** be committed to source control.
- Generation can be slow/costly depending on `BOOK_CHAPTERS`, `BOOK_PARAGRAPHS_PER_CHAPTER`, and the chosen `BOOK_MODEL`.
