from app.ai.intent_extractor import IntentExtractor
from app.ai.tool_dispatcher import ToolDispatcher


class AIAgentService:
    """Coordinates the complete AI workflow."""

    def __init__(self) -> None:
        self.intent_extractor = IntentExtractor()
        self.tool_dispatcher = ToolDispatcher()

    async def process(self, message: str):
        """
        Process a user message through the AI pipeline.
        """

        intent = await self.intent_extractor.extract(message)

        # Ask for missing information
        if intent.missing_fields:
            return {
                "success": True,
                "intent": intent.intent,
                "parameters": intent.parameters.model_dump(mode="json"),
                "missing_fields": intent.missing_fields,
                "reply": (
                    f"I need your {', '.join(intent.missing_fields)} "
                    "before I can search for buses."
                ),
                "trips": [],
            }

        # Execute backend tool
        trips = await self.tool_dispatcher.dispatch(intent)

        return {
            "success": True,
            "intent": intent.intent,
            "parameters": intent.parameters.model_dump(mode="json"),
            "missing_fields": [],
            "reply": "Trip search completed successfully.",
            "trips": trips,
        }