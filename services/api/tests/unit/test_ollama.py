import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from jurirag.domain.errors import LLMError, LLMGenerationError, LLMTimeoutError, LLMUnavailableError
from jurirag.domain.llm import ChatMessage, GenerationParams, ToolCall, ToolSpec
from jurirag.infrastructure.ollama import OllamaClient, OllamaEmbedder

BASE_URL = "http://ollama.test"
PARAMS = GenerationParams(
    model="qwen3.5:9b", temperature=0.1, seed=42, top_p=0.9, num_predict=256, num_ctx=8192
)
TOOL = ToolSpec(name="search_cases", description="d", parameters={"type": "object"})


@pytest.fixture
async def client() -> AsyncIterator[OllamaClient]:
    async with httpx.AsyncClient() as http:
        yield OllamaClient(http, BASE_URL)


@respx.mock
async def test_chat_sends_tools_think_and_options(client: OllamaClient) -> None:
    route = respx.post(f"{BASE_URL}/api/chat").respond(
        json={
            "model": "qwen3.5:9b",
            "message": {"content": "ok"},
            "prompt_eval_count": 12,
            "eval_count": 3,
        }
    )

    response = await client.chat([ChatMessage(role="user", content="q")], PARAMS, tools=[TOOL])

    sent = json.loads(route.calls.last.request.content)
    assert sent["think"] is False
    assert sent["tools"][0]["function"]["name"] == "search_cases"
    assert sent["options"]["temperature"] == 0.1
    assert response.prompt_tokens == 12 and response.completion_tokens == 3


@respx.mock
async def test_tool_calls_are_parsed_including_string_arguments(client: OllamaClient) -> None:
    respx.post(f"{BASE_URL}/api/chat").respond(
        json={
            "message": {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "search_cases", "arguments": {"query": "bail", "k": 5}}},
                    {"function": {"name": "read_case", "arguments": '{"case_id": "abc"}'}},
                    {"function": {"name": "read_case", "arguments": "pas du json"}},
                ],
            }
        }
    )

    response = await client.chat([ChatMessage(role="user", content="q")], PARAMS)

    assert response.tool_calls[0] == ToolCall(
        name="search_cases", arguments={"query": "bail", "k": 5}
    )
    assert response.tool_calls[1].arguments == {"case_id": "abc"}
    assert response.tool_calls[2].arguments == {"__raw__": "pas du json"}


@respx.mock
async def test_assistant_tool_calls_and_tool_results_are_sent_back(client: OllamaClient) -> None:
    route = respx.post(f"{BASE_URL}/api/chat").respond(json={"message": {"content": "ok"}})
    history = [
        ChatMessage(
            role="assistant", tool_calls=[ToolCall(name="read_case", arguments={"case_id": "x"})]
        ),
        ChatMessage(role="tool", content="{}", tool_name="read_case"),
    ]

    await client.chat(history, PARAMS)

    sent = json.loads(route.calls.last.request.content)["messages"]
    assert sent[0]["tool_calls"][0]["function"]["arguments"] == {"case_id": "x"}
    assert sent[1]["tool_name"] == "read_case"


@respx.mock
async def test_missing_message_field_is_a_generation_error(client: OllamaClient) -> None:
    respx.post(f"{BASE_URL}/api/chat").respond(json={"done": True})

    with pytest.raises(LLMGenerationError):
        await client.chat([ChatMessage(role="user", content="q")], PARAMS)


@respx.mock
async def test_non_json_body_is_a_generation_error(client: OllamaClient) -> None:
    respx.post(f"{BASE_URL}/api/chat").respond(text="<html>")

    with pytest.raises(LLMGenerationError):
        await client.chat([ChatMessage(role="user", content="q")], PARAMS)


@respx.mock
@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"side_effect": httpx.ConnectError("refused")}, LLMUnavailableError),
        ({"side_effect": httpx.ReadTimeout("slow")}, LLMTimeoutError),
        ({"status_code": 404, "json": {"error": "model not found"}}, LLMUnavailableError),
        ({"status_code": 500, "json": {"error": "boom"}}, LLMError),
    ],
)
async def test_server_errors_are_typed(client: OllamaClient, kwargs: dict, error: type) -> None:  # type: ignore[type-arg]
    route = respx.post(f"{BASE_URL}/api/chat")
    if "side_effect" in kwargs:
        route.side_effect = kwargs["side_effect"]
    else:
        route.respond(**kwargs)

    with pytest.raises(error):
        await client.chat([ChatMessage(role="user", content="q")], PARAMS)


@respx.mock
async def test_embedder_checks_vector_count() -> None:
    respx.post(f"{BASE_URL}/api/embed").respond(json={"embeddings": [[0.1, 0.2]]})
    async with httpx.AsyncClient() as http:
        embedder = OllamaEmbedder(http, BASE_URL, "qwen3-embedding:0.6b")
        assert await embedder.embed(["a"]) == [[0.1, 0.2]]
        with pytest.raises(LLMGenerationError):
            await embedder.embed(["a", "b"])
