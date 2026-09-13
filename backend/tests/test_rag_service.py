import pytest
from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_returns_grounded_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService(
        base_url="http://127.0.0.1:11434",
        model="test-model",
    )

    async def fake_generate(
        prompt: str,
    ) -> str:
        assert "BUSNBOX DOCUMENTS:" in prompt
        assert "miss" in prompt.lower()

        return (
            "Passengers should arrive before "
            "the reporting time. Missing the bus "
            "because of late arrival may not "
            "qualify for a refund."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What happens if I arrive late "
        "and miss my bus?"
    )

    assert result is not None
    assert result.answer
    assert "late" in result.answer.lower()
    assert result.source_ids
    assert "kb-boarding-time" in result.source_ids


@pytest.mark.asyncio
async def test_trip_search_bypasses_rag() -> None:
    service = RAGService()

    result = await service.answer(
        "Find buses from Chennai to "
        "Bangalore tomorrow"
    )

    assert result is None


@pytest.mark.asyncio
async def test_unrelated_question_bypasses_rag() -> None:
    service = RAGService()

    result = await service.answer(
        "Tell me a joke about computers"
    )

    assert result is None


@pytest.mark.asyncio
async def test_insufficient_model_answer_uses_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return "INSUFFICIENT_KNOWLEDGE"

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What is the luggage policy?"
    )

    assert result is not None
    assert result.answer
    assert "luggage" in result.answer.lower()


@pytest.mark.asyncio
async def test_hallucinated_policy_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "BusNBox always provides a 90% refund "
            "within exactly 24 hours."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What is the refund policy?"
    )

    assert result is not None
    assert result.answer
    assert "90%" not in result.answer
    assert "24 hours" not in result.answer


@pytest.mark.asyncio
async def test_hallucinated_price_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "The cancellation fee is exactly "
            "₹500 for every BusNBox booking."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What is the cancellation policy?"
    )

    assert result is not None
    assert result.answer
    assert "₹500" not in result.answer
    assert "500" not in result.answer


@pytest.mark.asyncio
async def test_kb_supported_numeric_claim_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "Refund processing may take several "
            "working days after it is initiated."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "How long does a refund take?"
    )

    assert result is not None
    assert "working days" in result.answer.lower()


@pytest.mark.asyncio
async def test_unsupported_numeric_claim_is_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "Refunds are processed within exactly "
            "2 hours and you will receive 100% "
            "of the amount."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "How long does a refund take?"
    )

    assert result is not None
    assert "2 hours" not in result.answer
    assert "100%" not in result.answer


@pytest.mark.asyncio
async def test_kb_supported_operator_condition_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "Luggage limits are determined by "
            "the bus operator."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What is the luggage limit?"
    )

    assert result is not None
    assert "operator" in result.answer.lower()


@pytest.mark.asyncio
async def test_fake_guarantee_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RAGService()

    async def fake_generate(
        prompt: str,
    ) -> str:
        return (
            "BusNBox guarantees that every "
            "passenger will receive a refund."
        )

    monkeypatch.setattr(
        service,
        "_generate_answer",
        fake_generate,
    )

    result = await service.answer(
        "What happens if I miss my bus?"
    )

    if result is not None:
        assert "guarantees" not in result.answer.lower()