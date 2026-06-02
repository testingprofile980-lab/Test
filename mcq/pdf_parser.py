"""PDF text extraction and chunking."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

import fitz  # pymupdf


@dataclass
class Chunk:
    index: int
    text: str
    page_start: int
    page_end: int


def extract_pages(pdf_bytes: bytes) -> list[str]:
    """Extract per-page text, trying sorted reading order first and falling
    back to block extraction for pages where sort-mode returns nothing.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        text = page.get_text("text", sort=True)
        if not text.strip():
            # Fallback: gather text blocks and join by reading-order
            blocks = page.get_text("blocks") or []
            blocks = sorted(
                [b for b in blocks if isinstance(b, (list, tuple)) and len(b) >= 5],
                key=lambda b: (round(b[1] / 10), b[0]),  # y then x
            )
            text = "\n".join(b[4] for b in blocks)
        pages.append(text)
    doc.close()
    return pages


def _clean(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)        # join hyphenated line-breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_repeated_lines(pages: list[str]) -> list[str]:
    """Remove lines that show up on at least half the pages (headers, footers,
    slide numbers, copyright lines). Skipped for PDFs with <4 pages.
    """
    if len(pages) < 4:
        return pages
    counts: Counter[str] = Counter()
    for p in pages:
        for raw in set(p.splitlines()):
            line = raw.strip()
            if 3 < len(line) < 80:
                counts[line] += 1
    threshold = max(3, len(pages) // 2)
    repeats = {line for line, c in counts.items() if c >= threshold}
    if not repeats:
        return pages
    out: list[str] = []
    for p in pages:
        kept = [ln for ln in p.splitlines() if ln.strip() not in repeats]
        out.append("\n".join(kept))
    return out


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
    pages = extract_pages(pdf_bytes)
    pages = _strip_repeated_lines(pages)
    return chunk_pages(pages, target_chars=target_chars)


def page_diagnostics(pdf_bytes: bytes) -> dict:
    """Quick stats so the UI can warn about image-only / sparse PDFs."""
    pages = extract_pages(pdf_bytes)
    chars_per_page = [len(p) for p in pages]
    empty = sum(1 for c in chars_per_page if c < 20)
    return {
        "page_count": len(pages),
        "total_chars": sum(chars_per_page),
        "empty_pages": empty,
        "median_chars": sorted(chars_per_page)[len(chars_per_page) // 2] if chars_per_page else 0,
    }
