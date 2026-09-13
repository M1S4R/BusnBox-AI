from app.schemas.chat import ChatParameters
from app.services.conversation_service import (
    ConversationContext,
    ConversationService,
)


def test_new_conversation_is_empty():
    service = ConversationService()

    context = service.get_context("chat-1")

    assert isinstance(context, ConversationContext)

    assert context.parameters.source is None
    assert context.parameters.destination is None
    assert context.parameters.travel_date is None
    assert context.parameters.filters == {}


def test_update_stores_parameters():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(
            source="Chennai",
        ),
    )

    context = service.get_context("chat-1")

    assert context.parameters.source == "Chennai"


def test_update_merges_fields():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(source="Chennai"),
    )

    service.update_context(
        "chat-1",
        ChatParameters(destination="Bangalore"),
    )

    context = service.get_context("chat-1")

    assert context.parameters.source == "Chennai"
    assert context.parameters.destination == "Bangalore"


def test_filters_are_merged():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(
            filters={
                "bus_type": "AC",
            }
        ),
    )

    service.update_context(
        "chat-1",
        ChatParameters(
            filters={
                "price": "cheap",
            }
        ),
    )

    context = service.get_context("chat-1")

    assert context.parameters.filters == {
        "bus_type": "AC",
        "price": "cheap",
    }


def test_clear_context():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(source="Chennai"),
    )

    service.clear_context("chat-1")

    context = service.get_context("chat-1")

    assert context.parameters.source is None


def test_conversations_are_isolated():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(source="Chennai"),
    )

    service.update_context(
        "chat-2",
        ChatParameters(source="Mumbai"),
    )

    first = service.get_context("chat-1")
    second = service.get_context("chat-2")

    assert first.parameters.source == "Chennai"
    assert second.parameters.source == "Mumbai"


def test_get_context_returns_copy():
    service = ConversationService()

    service.update_context(
        "chat-1",
        ChatParameters(source="Chennai"),
    )

    context = service.get_context("chat-1")

    context.parameters.source = "Changed"

    stored = service.get_context("chat-1")

    assert stored.parameters.source == "Chennai"