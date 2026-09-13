from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.ai.providers.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_provider_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = GeminiProvider()

    mock_generate_content = AsyncMock(
        return_value=SimpleNamespace(
            text="BUSNBOX",
        )
    )

    monkeypatch.setattr(
        provider._client.aio.models,
        "generate_content",
        mock_generate_content,
    )

    response = await provider.generate(
        "Reply with only the word BUSNBOX.",
        system_instruction=(
            "Follow the user's output formatting exactly."
        ),
    )

    assert response.upper() == "BUSNBOX"

    mock_generate_content.assert_awaited_once()