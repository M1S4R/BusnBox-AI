import os

import pytest
from app.ai.providers.gemini_provider import GeminiProvider

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_GEMINI_LIVE_TESTS") != "1",
    reason="Live Gemini tests are disabled.",
)
@pytest.mark.asyncio
async def test_gemini_provider_live_generation() -> None:
    provider = GeminiProvider()

    response = await provider.generate(
        "Reply with only the word BUSNBOX.",
        system_instruction=(
            "Follow the user's output formatting exactly."
        ),
    )

    assert response.strip().upper() == "BUSNBOX"