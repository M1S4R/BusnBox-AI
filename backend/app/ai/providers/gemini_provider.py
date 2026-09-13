import asyncio

from app.ai.providers.base_provider import BaseLLMProvider
from app.core.config import settings
from google import genai
from google.genai import types


class GeminiProvider(BaseLLMProvider):
    """Gemini implementation of the BusNBox LLM provider."""

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from the environment."
            )

        self._model = settings.gemini_model
        self._timeout_seconds = settings.gemini_timeout_seconds

        self._client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
    ) -> str:
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError("Prompt cannot be empty.")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._model,
                    contents=cleaned_prompt,
                    config=config,
                ),
                timeout=self._timeout_seconds,
            )

        except TimeoutError as exc:
            raise RuntimeError(
                "Gemini request timed out."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"Gemini request failed: {exc}"
            ) from exc

        response_text = response.text

        if not response_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response_text.strip()