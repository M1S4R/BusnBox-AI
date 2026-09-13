from app.services.knowledge_base_service import (
    knowledge_base_service,
)


def test_refund_policy_retrieval() -> None:
    matches = knowledge_base_service.search(
        "When will my refund reach my bank?"
    )

    assert matches
    assert (
        matches[0].document_id
        == "kb-refund-policy"
    )
    assert matches[0].score > 0


def test_luggage_policy_retrieval() -> None:
    matches = knowledge_base_service.search(
        "How much luggage can I carry?"
    )

    assert matches
    assert (
        matches[0].document_id
        == "kb-luggage-policy"
    )


def test_pet_policy_retrieval() -> None:
    matches = knowledge_base_service.search(
        "Can I travel with my dog?"
    )

    assert matches
    assert (
        matches[0].document_id
        == "kb-pet-policy"
    )


def test_payment_failure_retrieval() -> None:
    matches = knowledge_base_service.search(
        (
            "Money was deducted but my "
            "ticket was not confirmed"
        )
    )

    assert matches
    assert (
        matches[0].document_id
        == "kb-payment-failure"
    )


def test_unknown_question_returns_no_match() -> None:
    matches = knowledge_base_service.search(
        "Tell me a funny joke about computers"
    )

    assert matches == []


def test_context_builder() -> None:
    matches = knowledge_base_service.search(
        "What documents should I carry?"
    )

    context = (
        knowledge_base_service.build_context(
            matches
        )
    )

    assert context
    assert "Title:" in context
    assert "Content:" in context


def test_get_document() -> None:
    document = (
        knowledge_base_service.get_document(
            "kb-seat-selection"
        )
    )

    assert document is not None
    assert document.category == "seats"
