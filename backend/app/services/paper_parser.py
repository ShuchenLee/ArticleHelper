from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class PaperParseError(RuntimeError):
    """Raised when a paper cannot be parsed into text pages."""


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class ParsedPaper:
    title: str | None
    language: str
    pages: list[ParsedPage]


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(?=[A-Za-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def parse_pdf(path: Path | str) -> ParsedPaper:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise PaperParseError(f"PDF file does not exist: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise PaperParseError(f"Only PDF files are supported now: {pdf_path.name}")

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise PaperParseError("PyMuPDF is not installed. Run `pip install -r requirements.txt`.") from exc

    try:
        document = fitz.open(pdf_path)
    except Exception as exc:  # pragma: no cover - depends on PyMuPDF internals
        raise PaperParseError(f"Failed to open PDF: {pdf_path.name}") from exc

    pages: list[ParsedPage] = []
    try:
        for index, page in enumerate(document, start=1):
            text = normalize_text(page.get_text("text"))
            if text:
                pages.append(ParsedPage(page_number=index, text=text))
    finally:
        document.close()

    if not pages:
        raise PaperParseError("No extractable text found. OCR support is not implemented yet.")

    all_text = "\n".join(page.text for page in pages[:2])
    return ParsedPaper(
        title=guess_title(all_text),
        language=detect_language(all_text),
        pages=pages,
    )


def guess_title(text: str) -> str | None:
    lines = [
        line.strip()
        for line in text.splitlines()
        if 8 <= len(line.strip()) <= 220 and not _looks_like_section_heading(line.strip())
    ]
    if not lines:
        return None
    return lines[0]


def detect_language(text: str) -> str:
    sample = text[:4000]
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", sample))
    latin_count = len(re.findall(r"[A-Za-z]", sample))
    if cjk_count > latin_count * 0.25:
        return "zh"
    return "en"


def _looks_like_section_heading(line: str) -> bool:
    normalized = re.sub(r"^\d+(\.\d+)*\s*", "", line).strip().lower()
    return normalized in {
        "abstract",
        "introduction",
        "related work",
        "methods",
        "method",
        "experiments",
        "results",
        "discussion",
        "conclusion",
        "references",
    }
