"""Intégration réelle : Ollama démarré, modèles installés, index construit.

uv run pytest -m ollama -o addopts=""
"""

from collections.abc import AsyncIterator

import httpx
import pytest

from jurirag.application.agent.graph import AGENT_SYSTEM
from jurirag.application.agent.tools import READ_SPEC, SEARCH_SPEC, SearchCasesArgs
from jurirag.bootstrap import load_index, make_llm
from jurirag.config import get_settings
from jurirag.domain.errors import LLMUnavailableError
from jurirag.domain.llm import ChatMessage
from jurirag.infrastructure.ollama import OllamaClient

pytestmark = pytest.mark.ollama


@pytest.fixture
async def http() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=300) as client:
        yield client


async def test_models_are_installed(http: httpx.AsyncClient) -> None:
    settings = get_settings()
    models = await make_llm(settings, http).list_models()
    assert settings.ollama_model in models and settings.ollama_embed_model in models


async def test_model_proposes_a_valid_search_call(http: httpx.AsyncClient) -> None:
    settings = get_settings()
    response = await make_llm(settings, http).chat(
        [
            ChatMessage(role="system", content=AGENT_SYSTEM),
            ChatMessage(
                role="user",
                content="Un abandon de poste justifie-t-il un licenciement pour faute grave ?",
            ),
        ],
        settings.generation_params(),
        tools=[SEARCH_SPEC, READ_SPEC],
    )
    assert response.tool_calls and response.tool_calls[0].name == "search_cases"
    SearchCasesArgs.model_validate(response.tool_calls[0].arguments)
    assert response.prompt_tokens and response.completion_tokens


async def test_missing_model_is_reported(http: httpx.AsyncClient) -> None:
    settings = get_settings()
    params = settings.generation_params(model="modele-inexistant:1b")
    with pytest.raises(LLMUnavailableError):
        await OllamaClient(http, settings.ollama_base_url).chat(
            [ChatMessage(role="user", content="x")], params
        )


async def test_real_index_search_and_read(http: httpx.AsyncClient) -> None:
    bundle = load_index(get_settings(), http)
    hits = await bundle.retriever.search("licenciement faute grave salarié", k=5)
    assert len(hits) == 5
    case_id = hits[0].passage.case_id
    in_case = await bundle.retriever.search_in_case("dispositif cassation", case_id, 3)
    assert in_case and all(h.passage.case_id == case_id for h in in_case)
