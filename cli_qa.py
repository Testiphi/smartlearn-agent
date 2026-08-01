"""CLI Q&A Tool — ask questions about a multi-paragraph text via OpenRouter LLM.

Usage:
    python cli_qa.py
    Paste your text, type END on a new line, then enter your question.
"""

import argparse
import sys
from dotenv import load_dotenv
from openai import OpenAI
import os

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

MODEL = "qwen/qwen3.5-flash-02-23"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_text() -> str:
    """Read multi-line text from stdin until a line containing only 'END'."""
    print("Paste your text below. Type END on a new line when done:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def build_messages(text: str, question: str) -> list[dict]:
    """Build the system + user messages for the LLM call.

    Paragraphs are split by blank lines and numbered starting from 1.
    """
    # Normalize line endings and split into paragraphs
    normalized = text.replace("\r\n", "\n")
    raw_paragraphs = normalized.split("\n\n")
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    # Build the labelled text block
    labelled = "\n\n".join(
        f"[Paragraph {i}] {p}" for i, p in enumerate(paragraphs, start=1)
    )

    system_prompt = """You are a precise research assistant.

Rules:
1. Answer ONLY using information from the provided text.
2. After EVERY claim, add a citation in the format [Paragraph X].
3. If a sentence uses information from multiple paragraphs, cite all of them.
4. If the text does not contain the answer, reply:
    "The text does not provide this information."
5. Do NOT add any information beyond what is in the text.

Example:
If the text says:
[Paragraph 1] The sky is blue.
[Paragraph 2] Grass is green.

And the question is: 'What color is the sky?'
Your answer should be: 'The sky is blue [Paragraph 1].'
"""

    user_message = f"{labelled}\n\nQuestion: {question}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def ask(messages: list[dict]) -> str:
    """Send messages to the LLM and return the answer text."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # ---- Parse command-line arguments ----
    parser = argparse.ArgumentParser(description="CLI Q&A Tool")
    parser.add_argument(
        "--file",
        help="Path to a text file to use as input (instead of pasting)",
    )
    args = parser.parse_args()

    # ---- Read the source text ----
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"Read text from {args.file}.")
    else:
        text = read_text()

    # 2. Guard against empty input — do NOT call the API
    if not text.strip():
        print("Error: No text provided. Please paste some text and try again.")
        return

    # 3. Multi-turn Q&A loop
    while True:
        print()
        question = input("Your question (or 'quit' to exit): ").strip()
        if question.lower() == "quit":
            print("Goodbye!")
            break
        if not question:
            print("Error: No question provided.")
            continue

        # 4. Build prompts, call LLM, and print the answer
        print()
        messages = build_messages(text, question)
        answer = ask(messages)
        print(answer)


if __name__ == "__main__":
    main()
