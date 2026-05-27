"""PDF text extraction and chunking."""
from __future__ import annotations

import re
from dataclasses import dataclass

import fitz  # pymupdf


@dataclass
class Chunk:
    index: int
    text: str
    page_start: int
    page_end: int


def extract_pages(pdf_bytes: bytes) -> list[str]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return pages


def _clean(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)        # join hyphenated line-breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_pages(pages: list[str], target_chars: int = 4000) -> list[Chunk]:
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    start_page = 1

    for i, raw in enumerate(pages, start=1):
        page = _clean(raw)
        if not page:
            continue
        if buf_len + len(page) > target_chars and buf:
            chunks.append(Chunk(len(chunks), "\n\n".join(buf), start_page, i - 1))
            buf, buf_len, start_page = [], 0, i
        buf.append(page)
        buf_len += len(page)

    if buf:
        chunks.append(Chunk(len(chunks), "\n\n".join(buf), start_page, len(pages)))
    return chunks


def parse_pdf(pdf_bytes: bytes, target_chars: int = 4000) -> list[Chunk]:
    return chunk_pages(extract_pages(pdf_bytes), target_chars=target_chars)
