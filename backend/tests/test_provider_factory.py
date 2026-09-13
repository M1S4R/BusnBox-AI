from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.provider_factory import ProviderFactory


def test_provider_factory_returns_gemini() -> None:
    provider = ProviderFactory.get_provider()

    assert isinstance(provider, GeminiProvider)