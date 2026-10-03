"""Explain one fixed public help article; never send free-form user text."""

import asyncio

import httpx

from ssas.config.settings import Settings


class HelpProviderError(Exception):
    pass


class OpenAIHelpProvider:
    def __init__(self, config: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.config = config
        self.transport = transport

    async def explain(self, article: dict[str, str]) -> str:
        key = self.config.openai_api_key
        if key is None or not key.get_secret_value().strip():
            raise HelpProviderError("La IA no está configurada")
        payload = {
            "model": self.config.ia_model,
            "store": False,
            "max_output_tokens": 300,
            "instructions": (
                "Explica en español esta guía pública de SSAS RRHH de forma breve y clara. "
                "Usa solo el contenido entregado. No inventes funciones ni afirmes haber "
                "realizado acciones. Si no hay suficiente información, dilo."
            ),
            "input": f"Título: {article['titulo']}\nGuía: {article['texto']}",
        }
        try:
            async with asyncio.timeout(self.config.help_ai_timeout_seconds):
                async with httpx.AsyncClient(
                    timeout=self.config.help_ai_timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/responses",
                        headers={"Authorization": f"Bearer {key.get_secret_value()}"},
                        json=payload,
                    )
                    response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or body.get("status") != "completed":
                raise HelpProviderError("La IA no completó la respuesta")
            contents = [
                content
                for item in body.get("output", [])
                if item.get("type") == "message"
                for content in item.get("content", [])
            ]
            if any(item.get("type") == "refusal" for item in contents):
                raise HelpProviderError("La IA rechazó la solicitud")
            texts = [item["text"] for item in contents if item.get("type") == "output_text"]
            if len(texts) != 1 or not isinstance(texts[0], str) or not texts[0].strip():
                raise HelpProviderError("La IA devolvió una respuesta incompleta")
            return texts[0].strip()[:700]
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            raise HelpProviderError("La IA no está disponible") from exc
