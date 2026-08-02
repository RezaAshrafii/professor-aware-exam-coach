from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentError(ValueError):
    pass


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentError(f"Unsupported file type: {suffix}")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    elif suffix == ".docx":
        document = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        text = path.read_text(encoding="utf-8", errors="replace")

    text = normalize_text(text)
    if not text.strip():
        raise DocumentError("No readable text was found in the file.")
    return text


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, target_chars: int = 1800, overlap_chars: int = 220) -> list[str]:
    if len(text) <= target_chars:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > target_chars:
            chunks.append(current)
            overlap = current[-overlap_chars:] if overlap_chars else ""
            current = f"{overlap}\n\n{paragraph}".strip()
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks
