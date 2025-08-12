#!/usr/bin/env python3

"""
Dry run: extract and chunk text from a PDF without invoking TTS or LLMs.

Usage:
  python -B scripts/dry_run.py [path/to/file.pdf]
"""

import sys
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    import pdfplumber

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text += page_text + "\n"
    return text.strip()


def chunk_text(text: str, max_length: int = 4000):
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""
    sentences = text.replace("!", ".").replace("?", ".").split(".")

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        s += "."
        if len(current) + len(s) > max_length:
            if current:
                chunks.append(current.strip())
                current = s
            else:
                words = s.split()
                temp = ""
                for w in words:
                    if len(temp) + len(w) + 1 > max_length:
                        if temp:
                            chunks.append(temp.strip())
                            temp = w
                        else:
                            chunks.append(w[:max_length])
                            temp = w[max_length:]
                    else:
                        temp = (temp + " " + w) if temp else w
                if temp:
                    current = temp
        else:
            current = (current + " " + s) if current else s

    if current:
        chunks.append(current.strip())
    return chunks


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/test.pdf")
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"Reading: {pdf_path}")
    text = extract_text_from_pdf(str(pdf_path))
    if not text:
        print("No text extracted.")
        sys.exit(2)

    words = len(text.split())
    chars = len(text)
    print(f"Extracted chars: {chars}")
    print(f"Estimated words: {words}")

    chunks = chunk_text(text, 4000)
    print(f"Chunks: {len(chunks)}")
    if chunks:
        print(f"First chunk length: {len(chunks[0])}")
        preview = chunks[0][:300].replace("\n", " ")
        print(f"Preview: {preview}...")


if __name__ == "__main__":
    main()

