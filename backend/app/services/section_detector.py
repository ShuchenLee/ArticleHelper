from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.paper_parser import ParsedPage


KNOWN_SECTIONS = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "background": "Background",
    "related work": "Related Work",
    "method": "Methods",
    "methods": "Methods",
    "methodology": "Methods",
    "materials and methods": "Methods",
    "experiments": "Experiments",
    "experimental setup": "Experiments",
    "evaluation": "Experiments",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
    "limitations": "Limitations",
    "references": "References",
}


@dataclass(frozen=True)
class SectionSpan:
    title: str
    page_start: int
    page_end: int
    text: str


def detect_sections(pages: list[ParsedPage]) -> list[SectionSpan]:
    sections: list[SectionSpan] = []
    current_title = "Front Matter"
    current_page_start = pages[0].page_number if pages else 1
    current_page_end = current_page_start
    current_lines: list[str] = []

    for page in pages:
        for line in page.text.splitlines():
            heading = normalize_heading(line)
            if heading and current_lines:
                sections.append(
                    SectionSpan(
                        title=current_title,
                        page_start=current_page_start,
                        page_end=current_page_end,
                        text="\n".join(current_lines).strip(),
                    )
                )
                current_title = heading
                current_page_start = page.page_number
                current_lines = [line.strip()]
            else:
                if heading:
                    current_title = heading
                    current_page_start = page.page_number
                current_lines.append(line.strip())
            current_page_end = page.page_number

    if current_lines:
        sections.append(
            SectionSpan(
                title=current_title,
                page_start=current_page_start,
                page_end=current_page_end,
                text="\n".join(current_lines).strip(),
            )
        )

    return [section for section in sections if section.text]


def normalize_heading(line: str) -> str | None:
    compact = " ".join(line.strip().split())
    if not compact or len(compact) > 80:
        return None

    lowered = compact.lower().rstrip(":")
    lowered = re.sub(r"^\d+(\.\d+)*\.?\s+", "", lowered)
    lowered = re.sub(r"^[ivxlcdm]+\.?\s+", "", lowered)
    return KNOWN_SECTIONS.get(lowered)
