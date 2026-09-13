import httpx
from app.core.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def generate(
        self,
        prompt: str,
        *,
        format_json: bool = False,
    ) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if format_json:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        generated_text = data.get("response")

        if not isinstance(generated_text, str):
            raise TypeError("Ollama returned a non-string response.")

        return generated_text