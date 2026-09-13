from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.core.config import settings


class ProviderFactory:
    """Create the configured LLM provider."""

    @staticmethod
    def get_provider() -> BaseLLMProvider:
        provider_name = settings.ai_provider.strip().lower()

        if provider_name == "gemini":
            return GeminiProvider()

        raise ValueError(
            f"Unsupported AI provider: {provider_name}"
        )