from app.models.domain import ChunkRecord
from app.services.chat_agent import answer_from_paper


def _chunk(index: int, section: str, text: str) -> ChunkRecord:
    return ChunkRecord(
        id=f"chunk-{index}",
        paper_id="paper-1",
        section=section,
        page_start=index + 1,
        page_end=index + 1,
        chunk_index=index,
        text=text,
    )


def test_answer_from_paper_returns_citations_for_retrieval_question():
    chunks = [
        _chunk(0, "Methods", "The method uses retrieval augmented generation to answer questions."),
        _chunk(1, "Conclusion", "The paper concludes with limitations."),
    ]

    answer = answer_from_paper("What method answers questions?", title="Paper", chunks=chunks)

    assert answer.citations
    assert answer.citations[0].section == "Methods"
    assert "Methods" in answer.answer


def test_answer_from_paper_handles_overview_question():
    chunks = [
        _chunk(0, "Abstract", "This paper studies literature reading agents."),
        _chunk(1, "Methods", "The method retrieves evidence."),
    ]

    answer = answer_from_paper("请总结这篇文章", title="Paper", chunks=chunks)

    assert "标题：Paper" in answer.answer
    assert answer.citations


def test_answer_from_paper_uses_selected_text_directly():
    answer = answer_from_paper(
        "解释这段",
        title=None,
        chunks=[],
        selected_text="A selected paragraph explains the experiment.",
    )

    assert "selected paragraph" in answer.answer
    assert answer.citations == []
