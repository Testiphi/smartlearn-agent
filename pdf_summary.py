"""PDF Summary Tool — extract text from a PDF and print a structured LLM summary.

Usage:
    python pdf_summary.py <path-to-pdf> [--pages START-END]
"""

import argparse
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise SystemExit("OPENROUTER_API_KEY is missing. Add it to .env and try again.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = "google/gemma-4-26b-a4b-it:free"


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------
def extract_text(pdf_path: str, start: int = 1, end: int | None = None) -> str:
    """Return the text of *pdf_path* with each page prefixed by [Page N].

    Only pages in [*start*, *end*] (inclusive) are extracted.  Returns an empty
    string when the selected range has no extractable text.
    """
    import fitz  # PyMuPDF — lazy import so missing-file errors come first

    doc = fitz.open(pdf_path)
    total = len(doc)
    if end is None:
        end = total

    pages: list[str] = []
    for i in range(start, end + 1):
        if i < 1 or i > total:
            continue  # skip pages outside the document
        text = doc[i - 1].get_text()
        if text.strip():
            pages.append(f"[Page {i}]\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a precise academic summariser. You receive the full text of a \
PDF document with pages labelled [Page N].

Output EXACTLY three sections with these headings and nothing else:

Overview
    A 2-4 sentence summary of what this document is about.

Key Points
    - Bullet list of the most important facts or arguments.
    - Every bullet MUST end with a citation like [Page X].
    - Use only pages that actually contain the cited information.

Limitations
    - 1-3 bullet points noting what the document does NOT cover, assumptions it makes, \
or information that seems incomplete."""


def build_messages(pdf_text: str) -> list[dict]:
    """Build system + user messages with the extracted PDF text."""
    user_message = (
        "Here is the document text.  Produce the three sections now.\n\n"
        + pdf_text
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def summarise(messages: list[dict]) -> str:
    """Send messages to the LLM and return the summary text."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def parse_page_range(range_str: str) -> tuple[int, int]:
    """Parse 'START-END' into (start, end).  Raises ValueError on bad input."""
    parts = range_str.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid page range '{range_str}'. Expected format: START-END (e.g. 1-5).")
    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid page range '{range_str}'. Both START and END must be numbers.")
    if start < 1:
        raise ValueError(f"Invalid page range '{range_str}'. START must be >= 1.")
    if start > end:
        raise ValueError(f"Invalid page range '{range_str}'. START must be <= END.")
    return start, end


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise a PDF via an LLM.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument(
        "--pages",
        help="Page range to summarise, e.g. 1-5",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: '{args.pdf}' does not exist or is not a file.")
        sys.exit(1)

    start, end = 1, None
    if args.pages:
        try:
            start, end = parse_page_range(args.pages)
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

    text = extract_text(args.pdf, start=start, end=end)

    if not text.strip():
        print(
            "This PDF contains no extractable text in the selected pages. "
            "It may be a scanned document — consider using OCR software first."
        )
        return

    messages = build_messages(text)
    summary = summarise(messages)
    print(summary)


if __name__ == "__main__":
    main()
