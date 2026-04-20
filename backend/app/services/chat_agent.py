from __future__ import annotations

from dataclasses import dataclass

from app.models.domain import ChunkRecord
from app.services.retrieval_service import SearchResult, search_chunks
from app.services.summary_service import build_paper_overview, compact_snippet


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    section: str | None
    page_start: int
    page_end: int


@dataclass(frozen=True)
class ChatAnswer:
    answer: str
    citations: list[Citation]


def answer_from_paper(
    message: str,
    *,
    title: str | None,
    chunks: list[ChunkRecord],
    selected_text: str | None = None,
    top_k: int = 4,
) -> ChatAnswer:
    if selected_text:
        return ChatAnswer(
            answer=_answer_selected_text(selected_text),
            citations=[],
        )

    if _is_overview_question(message):
        overview = build_paper_overview(title, chunks)
        citations = [
            _citation(chunk)
            for chunk in chunks
            if chunk.section in {"Abstract", "Methods", "Results", "Experiments", "Conclusion"}
        ][:4]
        return ChatAnswer(answer=_format_overview(overview), citations=citations)

    results = search_chunks(message, chunks, top_k=top_k)
    if not results:
        return ChatAnswer(
            answer=(
                "我在当前论文文本中没有检索到足够相关的依据。"
                "可以换一种问法，或指定页码、章节、选中的原文段落。"
            ),
            citations=[],
        )

    return ChatAnswer(
        answer=_format_evidence_answer(message, results),
        citations=[_citation(result.chunk) for result in results],
    )


def _is_overview_question(message: str) -> bool:
    lowered = message.lower()
    keywords = ["summary", "summarize", "overview", "main contribution", "总结", "概括", "主要贡献"]
    return any(keyword in lowered for keyword in keywords)


def _answer_selected_text(selected_text: str) -> str:
    snippet = compact_snippet(selected_text, max_chars=900)
    return (
        "这段原文的核心意思可以先这样理解：\n\n"
        f"{snippet}\n\n"
        "当前版本先做基于原文的抽取式解释；下一步接入大模型后，可以进一步提供术语解释、长句拆解和批判性分析。"
    )


def _format_evidence_answer(message: str, results: list[SearchResult]) -> str:
    lines = [
        "根据当前论文中检索到的相关片段，可以先定位到以下依据：",
        "",
    ]
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        page = _format_page_range(chunk.page_start, chunk.page_end)
        section = chunk.section or "Unknown section"
        lines.append(f"{index}. {section}，{page}")
        lines.append(f"   {compact_snippet(chunk.text, max_chars=380)}")
        lines.append("")
    lines.append(
        "基于这些片段，建议下一步接入 LLM 生成综合性回答；当前模块已经完成证据检索和引用返回。"
    )
    return "\n".join(lines).strip()


def _format_overview(overview) -> str:
    parts = []
    if overview.title:
        parts.append(f"标题：{overview.title}")
    if overview.abstract:
        parts.append(f"摘要：{overview.abstract}")
    if overview.methods:
        parts.append(f"方法：{overview.methods}")
    if overview.results:
        parts.append(f"结果/实验：{overview.results}")
    if overview.conclusion:
        parts.append(f"结论：{overview.conclusion}")
    if overview.limitations:
        parts.append(f"局限性：{overview.limitations}")
    if not parts:
        return "当前论文还没有足够的结构化内容可总结。"
    return "\n\n".join(parts)


def _citation(chunk: ChunkRecord) -> Citation:
    return Citation(
        chunk_id=chunk.id,
        section=chunk.section,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
    )


def _format_page_range(page_start: int, page_end: int) -> str:
    if page_start == page_end:
        return f"第 {page_start} 页"
    return f"第 {page_start}-{page_end} 页"
