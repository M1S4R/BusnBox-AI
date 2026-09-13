from copy import deepcopy
from dataclasses import dataclass, field

from app.schemas.chat import ChatParameters


@dataclass
class ConversationContext:
    parameters: ChatParameters = field(
        default_factory=ChatParameters
    )


class ConversationService:
    def __init__(self) -> None:
        self._conversations: dict[
            str,
            ConversationContext,
        ] = {}

    def get_context(
        self,
        conversation_id: str | None,
    ) -> ConversationContext:
        if not conversation_id:
            return ConversationContext()

        context = self._conversations.get(conversation_id)

        if context is None:
            context = ConversationContext()
            self._conversations[conversation_id] = context

        return deepcopy(context)

    def update_context(
        self,
        conversation_id: str | None,
        new_parameters: ChatParameters,
    ) -> ConversationContext:
        if not conversation_id:
            return ConversationContext(
                parameters=new_parameters
            )

        current_context = self._conversations.get(
            conversation_id,
            ConversationContext(),
        )

        merged_parameters = self.merge_parameters(
            current=current_context.parameters,
            incoming=new_parameters,
        )

        updated_context = ConversationContext(
            parameters=merged_parameters
        )

        self._conversations[conversation_id] = updated_context

        return deepcopy(updated_context)

    def clear_context(
        self,
        conversation_id: str | None,
    ) -> None:
        if conversation_id:
            self._conversations.pop(
                conversation_id,
                None,
            )

    @staticmethod
    def merge_parameters(
        current: ChatParameters,
        incoming: ChatParameters,
    ) -> ChatParameters:
        merged_filters = {
            **current.filters,
            **incoming.filters,
        }

        return ChatParameters(
            source=(
                incoming.source
                if incoming.source is not None
                else current.source
            ),
            destination=(
                incoming.destination
                if incoming.destination is not None
                else current.destination
            ),
            travel_date=(
                incoming.travel_date
                if incoming.travel_date is not None
                else current.travel_date
            ),
            filters=merged_filters,
        )


conversation_service = ConversationService()
