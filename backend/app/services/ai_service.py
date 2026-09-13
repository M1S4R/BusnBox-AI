import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.provider_factory import ProviderFactory
from app.schemas.chat import ChatIntent, ChatParameters


class AIServiceError(Exception):
    """Raised when AI analysis or generation fails."""


class AIAnalysisResult(BaseModel):
    intent: ChatIntent
    reply: str
    parameters: ChatParameters = Field(default_factory=ChatParameters)


class AIService:
    MAX_ATTEMPTS = 2

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self.provider = provider or ProviderFactory.get_provider()

    async def analyze_message(
        self,
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        cleaned_message = message.strip()

        if not cleaned_message:
            raise AIServiceError("Message cannot be empty.")

        parameters = current_parameters or ChatParameters()
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            prompt = self._build_contextual_message(
                message=cleaned_message,
                current_parameters=parameters,
            )

            if attempt > 1:
                prompt += (
                    "\n\nIMPORTANT: The previous response could not be "
                    "validated. Return exactly one valid JSON object using "
                    "the required schema. Do not include Markdown, code "
                    "fences, or additional text."
                )

            try:
                raw_response = await self.provider.generate(
                    prompt,
                    system_instruction=self._build_system_prompt(),
                )

                if not isinstance(raw_response, str):
                    raise TypeError(
                        "The AI provider returned non-string content."
                    )

                cleaned_response = raw_response.strip()

                if not cleaned_response:
                    raise ValueError(
                        "The AI provider returned empty content."
                    )

                parsed_content = self._parse_structured_content(
                    cleaned_response
                )

                normalized_content = self._normalize_analysis_data(
                    parsed_content
                )

                return AIAnalysisResult.model_validate(
                    normalized_content
                )

            except (
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
                ValidationError,
            ) as exc:
                last_error = exc

            except Exception as exc:
                raise AIServiceError(
                    "The configured AI provider request failed."
                ) from exc

        raise AIServiceError(
            "The AI provider returned an invalid structured response."
        ) from last_error

    async def generate_reply(self, message: str) -> str:
        result = await self.analyze_message(
            message=message,
            current_parameters=ChatParameters(),
        )
        return result.reply

    async def summarize_search_results(
        self,
        user_message: str,
        trips: list[dict[str, Any]],
    ) -> str:
        del user_message

        if not trips:
            return (
                "Sorry, I couldn't find any buses matching your search."
            )

        prices: list[float] = []

        for trip in trips:
            price_candidates = [
                trip.get("price"),
                trip.get("fare"),
                trip.get("starting_price"),
                trip.get("minimum_price"),
            ]

            for candidate in price_candidates:
                parsed_price = self._parse_price(candidate)

                if parsed_price is not None:
                    prices.append(parsed_price)

        cheapest_price = min(prices) if prices else None

        if cheapest_price is not None:
            formatted_price: int | float

            if cheapest_price.is_integer():
                formatted_price = int(cheapest_price)
            else:
                formatted_price = cheapest_price

            return (
                f"I found {len(trips)} matching buses. "
                f"Fares start from ₹{formatted_price}."
            )

        return f"I found {len(trips)} matching buses."

    @staticmethod
    def _build_contextual_message(
        *,
        message: str,
        current_parameters: ChatParameters,
    ) -> str:
        context = {
            "source": current_parameters.source,
            "destination": current_parameters.destination,
            "travel_date": current_parameters.travel_date,
            "filters": current_parameters.filters or {},
        }

        return (
            "Current bus-search state:\n"
            f"{json.dumps(context, ensure_ascii=False)}\n\n"
            "Interpret the new message using this state. Return only values "
            "newly stated or changed by the user. Do not repeat stored values "
            "unless the user explicitly changes them.\n\n"
            f"New user message:\n{message}"
        )

    @classmethod
    def _parse_structured_content(
        cls,
        content: str,
    ) -> dict[str, Any]:
        cleaned = cls._remove_code_fences(content)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = json.loads(cls._extract_json_object(cleaned))

        if not isinstance(parsed, dict):
            raise TypeError("Structured response must be an object.")

        return parsed

    @staticmethod
    def _remove_code_fences(content: str) -> str:
        cleaned = content.strip()
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @staticmethod
    def _extract_json_object(content: str) -> str:
        start_index = content.find("{")
        end_index = content.rfind("}")

        if (
            start_index == -1
            or end_index == -1
            or end_index <= start_index
        ):
            raise ValueError("No JSON object found in response.")

        return content[start_index : end_index + 1]

    @staticmethod
    def _normalize_analysis_data(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(data)
        raw_intent = normalized.get("intent", "unknown")

        if isinstance(raw_intent, str):
            intent_key = (
                raw_intent.strip()
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            intent_aliases = {
                "search": "search_bus",
                "bus_search": "search_bus",
                "search_buses": "search_bus",
                "find_bus": "search_bus",
                "find_buses": "search_bus",
                "greet": "greeting",
                "hello": "greeting",
                "other": "unknown",
            }

            normalized["intent"] = intent_aliases.get(
                intent_key,
                intent_key,
            )

        reply = normalized.get("reply")

        if not isinstance(reply, str):
            normalized["reply"] = (
                "How can I help with your bus journey?"
            )
        else:
            normalized["reply"] = (
                reply.strip()
                or "How can I help with your bus journey?"
            )

        parameters = normalized.get("parameters")

        if not isinstance(parameters, dict):
            parameters = {}

        filters = parameters.get("filters")

        if not isinstance(filters, dict):
            filters = {}

        normalized["parameters"] = {
            "source": AIService._normalize_optional_text(
                parameters.get("source")
            ),
            "destination": AIService._normalize_optional_text(
                parameters.get("destination")
            ),
            "travel_date": AIService._normalize_optional_text(
                parameters.get("travel_date")
            ),
            "filters": filters,
        }

        return normalized

    @staticmethod
    def _normalize_optional_text(value: Any) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        cleaned = value.strip()

        if not cleaned or cleaned.casefold() in {
            "null",
            "none",
            "unknown",
            "not provided",
            "not specified",
        }:
            return None

        return cleaned

    @staticmethod
    def _parse_price(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return None

        cleaned = "".join(
            character
            for character in value
            if character.isdigit() or character == "."
        )

        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are BnB AI, the BusNBox bus travel assistant.

Analyze the user's message and return only one valid JSON object.

Allowed intent values:

"greeting"
Use when the user says hello, hi, hey, good morning,
or another greeting.

"search_bus"
Use when the user starts a new bus search or supplies
missing search information such as source, destination,
travel date, or filters.

"update_search"
Use when the user explicitly changes an existing search,
such as changing the source, destination, date, or replacing
an existing filter.

"clear_search"
Use when the user asks to start over, reset the search,
clear the current search, or begin again.

"remove_filter"
Use when the user asks to remove one or more filters from
the existing search.

"help"
Use when the user asks what BnB AI can do or how to use it.

"faq"
Use for general bus travel questions that are not an
inventory search.

"unknown"
Use when the message is unrelated to bus travel or unclear.

Return exactly this structure:

{
  "intent": "greeting",
  "reply": "Short helpful reply",
  "parameters": {
    "source": null,
    "destination": null,
    "travel_date": null,
    "filters": {}
  }
}

Rules:

1. intent must be exactly one of:
   greeting, search_bus, update_search,
   clear_search, remove_filter, help,
   faq, unknown

2. For search_bus, extract:
   source
   destination
   travel_date

3. Keep relative dates unchanged, including:
   today
   tomorrow
   next Friday

4. Store preferences inside filters.

5. Supported filters:
   operator
   bus_type
   maximum_price
   minimum_seats
   departure_time

6. Use numbers for numeric filter values.

7. Never invent missing information.

8. Missing source, destination, or travel_date must be null.

9. filters must always be a JSON object.

10. reply must be concise.

11. Do not return Markdown.

12. Do not return code fences.

13. Do not include text before or after the JSON object.

14. Follow-up messages that add missing information
    must use search_bus.

15. Explicit changes such as:
    "change destination to Mysore",
    "tomorrow instead",
    "make it Friday",
    or "show non-AC instead"
    must use update_search.

16. Requests such as:
    "start over",
    "reset search",
    "clear everything",
    or "begin again"
    must use clear_search.

17. Requests such as:
    "remove AC filter",
    "remove price limit",
    or "show all bus types"
    must use remove_filter.

18. If source and destination exist but travel_date is
    missing, interpret a date or relative date as
    travel_date.

19. A short answer that fills a missing search field must
    use the search_bus intent.

20. Return only newly supplied or explicitly changed
    parameter values. Keep all other parameter fields null
    and filters empty. The backend merges these values with
    the stored conversation state.

21. Never swap source and destination. Never overwrite a
    stored value unless the user clearly asks to change it.

22. For update_search, return only fields that the user
    explicitly changed. Leave all unchanged fields null
    and filters empty.

23. For clear_search, return empty parameters:

{
  "source": null,
  "destination": null,
  "travel_date": null,
  "filters": {}
}

24. For remove_filter, include the filter key with a null
    value. The backend will remove that key.

25. Never clear or overwrite stored values unless the user
    explicitly requests it.

Contextual example:

Current bus-search state:
{"source":"Chennai","destination":null,"travel_date":null,"filters":{}}

New user message:
Bangalore

Output:

{
  "intent": "search_bus",
  "reply": "Got it. What date would you like to travel?",
  "parameters": {
    "source": null,
    "destination": "Bangalore",
    "travel_date": null,
    "filters": {}
  }
}

Example input:

Find AC sleeper buses from Chennai to Bangalore
tomorrow under 1500 rupees

Example output:

{
  "intent": "search_bus",
  "reply": "I will search for matching buses.",
  "parameters": {
    "source": "Chennai",
    "destination": "Bangalore",
    "travel_date": "tomorrow",
    "filters": {
      "bus_type": "AC sleeper",
      "maximum_price": 1500
    }
  }
}
""".strip()