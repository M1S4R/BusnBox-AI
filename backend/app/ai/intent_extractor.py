import json
from datetime import UTC, date, datetime

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.provider_factory import ProviderFactory
from app.schemas.ai_intent import IntentExtractionResult
from pydantic import ValidationError


class IntentExtractionError(Exception):
    """Raised when the AI returns invalid intent data."""


class IntentExtractor:
    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self.provider = provider or ProviderFactory.get_provider()

    async def extract(
        self,
        message: str,
        *,
        today: date | None = None,
    ) -> IntentExtractionResult:
        cleaned_message = message.strip()

        if not cleaned_message:
            raise ValueError("Message cannot be empty.")

        current_date = today or datetime.now(UTC).date()

        prompt = self._build_prompt(
            message=cleaned_message,
            current_date=current_date,
        )

        raw_response = await self.provider.generate(
            prompt,
            system_instruction=(
                "You are an intent extraction engine for BusNBox. "
                "Return only valid JSON. "
                "Do not include Markdown, code fences, or explanations."
            ),
        )

        cleaned_response = self._clean_json_response(raw_response)

        try:
            parsed = json.loads(cleaned_response)

            return IntentExtractionResult.model_validate(
                parsed,
            )

        except (json.JSONDecodeError, ValidationError) as exc:
            raise IntentExtractionError(
                "The AI returned invalid intent JSON."
            ) from exc

    @staticmethod
    def _clean_json_response(
        raw_response: str,
    ) -> str:
        cleaned = raw_response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json")
            cleaned = cleaned.removesuffix("```")
            cleaned = cleaned.strip()

        elif cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```")
            cleaned = cleaned.removesuffix("```")
            cleaned = cleaned.strip()

        return cleaned

    @staticmethod
    def _build_prompt(
        message: str,
        current_date: date,
    ) -> str:
        return f"""
You are an intent extraction system for BusNBox, a bus-search assistant.

Current date: {current_date.isoformat()}

Identify exactly one intent:

- search_trip
- greeting
- help
- unknown

For search_trip, extract:

- source
- destination
- travel_date
- bus_type
- max_fare

Rules:

1. Return valid JSON only.
2. Do not include Markdown.
3. Do not invent missing information.
4. Convert dates to YYYY-MM-DD.
5. Interpret relative dates using the current date.
6. Use null for unavailable optional values.
7. missing_fields should only contain required search fields:
   source, destination, travel_date.
8. For greeting, help, and unknown intents, return empty parameters.
9. max_fare must be a number or null.
10. Use exactly one of the allowed intent values.
11. Do not add extra fields.

Required JSON shape:

{{
  "intent": "search_trip",
  "parameters": {{
    "source": "Chennai",
    "destination": "Bangalore",
    "travel_date": "2026-07-25",
    "bus_type": null,
    "max_fare": null
  }},
  "missing_fields": []
}}

User message:
{message}
""".strip()