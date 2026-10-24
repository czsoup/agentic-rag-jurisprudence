"""Adapters Ollama : génération (avec appels d'outils) et embeddings.

Gestion d'erreurs typées, étendue
aux outils, au paramètre `think`, aux comptes de tokens et à l'endpoint `/api/embed`.
"""

import json
import logging
import time
from collections.abc import Sequence
from typing import Any

import httpx

from jurirag.domain.errors import (
    LLMError,
    LLMGenerationError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from jurirag.domain.llm import ChatMessage, GenerationParams, LLMResponse, ToolCall, ToolSpec

logger = logging.getLogger(__name__)


def _message_payload(message: ChatMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {"function": {"name": call.name, "arguments": call.arguments}}
            for call in message.tool_calls
        ]
    if message.tool_name:
        payload["tool_name"] = message.tool_name
    return payload


def _parse_tool_calls(raw: Any) -> list[ToolCall]:
    """Convertit les appels proposés par le modèle. Les entrées mal formées sont écartées
    ici et signalées par un appel au nom vide, que l'agent traitera comme une erreur."""
    calls: list[ToolCall] = []
    for item in raw or []:
        function = item.get("function", {}) if isinstance(item, dict) else {}
        name = function.get("name")
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):  # certains modèles renvoient une chaîne JSON
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"__raw__": arguments}
        if not isinstance(arguments, dict):
            arguments = {"__raw__": arguments}
        calls.append(ToolCall(name=name if isinstance(name, str) else "", arguments=arguments))
    return calls


class OllamaClient:
    def __init__(self, http: httpx.AsyncClient, base_url: str, keep_alive: str = "30m") -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._keep_alive = keep_alive

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams,
        tools: Sequence[ToolSpec] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": params.model,
            "messages": [_message_payload(m) for m in messages],
            "stream": False,
            "think": params.think,
            "keep_alive": self._keep_alive,
            "options": {
                "temperature": params.temperature,
                "seed": params.seed,
                "top_p": params.top_p,
                "num_predict": params.num_predict,
                "num_ctx": params.num_ctx,
            },
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
        if response_schema is not None:
            payload["format"] = response_schema

        start = time.perf_counter()
        data = await self._request("POST", "/api/chat", json=payload)
        latency_ms = (time.perf_counter() - start) * 1000

        message = data.get("message")
        if not isinstance(message, dict):
            raise LLMGenerationError("Réponse d'Ollama sans champ `message`")
        # `message.thinking` (raisonnement interne) est volontairement ignoré : jamais affiché.
        return LLMResponse(
            content=str(message.get("content") or ""),
            tool_calls=_parse_tool_calls(message.get("tool_calls")),
            latency_ms=latency_ms,
            model=str(data.get("model", params.model)),
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )

    async def list_models(self) -> list[str]:
        data = await self._request("GET", "/api/tags")
        return [model["name"] for model in data.get("models", [])]

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = await self._http.request(method, self._base_url + path, **kwargs)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Ollama n'a pas répondu à temps ({path})") from exc
        except httpx.TransportError as exc:
            raise LLMUnavailableError(
                f"Ollama injoignable sur {self._base_url} — lancer `ollama serve`"
            ) from exc

        if response.status_code == httpx.codes.NOT_FOUND:
            raise LLMUnavailableError(
                f"Modèle introuvable sur Ollama ({response.text}) — lancer `ollama pull <modèle>`"
            )
        if response.is_error:
            raise LLMError(f"Ollama a répondu {response.status_code} : {response.text}")
        try:
            result: dict[str, Any] = response.json()
        except ValueError as exc:
            raise LLMGenerationError("Réponse d'Ollama non JSON") from exc
        return result


class OllamaEmbedder:
    """Embeddings via `/api/embed`. Vecteurs renvoyés tels quels (normalisés côté index)."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, model: str) -> None:
        self._client = OllamaClient(http, base_url)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        data = await self._client._request(
            "POST", "/api/embed", json={"model": self._model, "input": list(texts)}
        )
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise LLMGenerationError("Réponse d'embedding inattendue")
        return embeddings
