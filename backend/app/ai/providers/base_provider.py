from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Common interface for all BusNBox LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
    ) -> str:
        """Generate and return a plain-text model response."""
        raise NotImplementedError