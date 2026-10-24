"""API de bout en bout, sans Ollama ni index réels (doublures injectées dans le conteneur)."""

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from jurirag.application.agent.graph import AgentConfig, AgentGraph
from jurirag.application.agent.runner import AgentRunner
from jurirag.application.agent.tools import CaseTools, ToolExecutor
from jurirag.config import Settings
from jurirag.interfaces.http.app import create_app
from tests.conftest import MemoryCases, ScriptedLLM, WordRetriever, reply
from tests.unit.test_agent_graph import PARAMS, judge

DOWN = "http://127.0.0.1:9"  # port fermé : Ollama « arrêté »


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path, ollama_base_url=DOWN, hitl_timeout_s=60)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_health_explains_what_is_missing(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["status"] == "degraded"
    assert body["checks"] == {
        "ollama": False,
        "generation_model": False,
        "embedding_model": False,
        "index": False,
    }
    assert any("ollama serve" in p for p in body["problems"])
    assert any("make index" in p for p in body["problems"])


def test_routes_needing_the_index_answer_503(client: TestClient) -> None:
    assert client.get("/api/v1/cases/search", params={"q": "bail"}).status_code == 503
    response = client.post("/api/v1/runs", json={"session_id": "abcd", "question": "Question ?"})
    assert response.status_code == 503 and "make index" in response.json()["detail"]


def test_invalid_payload_is_rejected(client: TestClient) -> None:
    assert (
        client.post(
            "/api/v1/runs", json={"session_id": "../x", "question": "Question ?"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/runs", json={"session_id": "abcd", "question": "?", "mode": "x"}
        ).status_code
        == 422
    )


@pytest.fixture
def agent_client(client: TestClient, cases: MemoryCases, retriever: WordRetriever) -> TestClient:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "licenciement faute grave"})),
            reply("La Cour rejette le pourvoi formé par le salarié [P1]."),
            judge("supports"),
        ]
    )
    container = client.app.state.container  # type: ignore[attr-defined]
    cfg = AgentConfig(params=PARAMS, judge_params=PARAMS)
    saver = InMemorySaver()
    graph = (
        AgentGraph(llm, ToolExecutor(CaseTools(retriever, cases)), cases, cfg)
        .builder()
        .compile(checkpointer=saver)
    )
    container.index = object()  # l'index réel n'est pas utilisé : outils branchés sur la doublure
    container.runner = AgentRunner({"single": graph}, saver, container.runs, "qwen3.5:9b", 60)
    return client


def _lines(response: Any) -> list[dict[str, Any]]:
    return [json.loads(line) for line in response.text.splitlines() if line.strip()]


def test_run_streams_ndjson_events_then_final_status(agent_client: TestClient) -> None:
    response = agent_client.post(
        "/api/v1/runs", json={"session_id": "sess-1", "question": "Faute grave ?"}
    )

    assert response.headers["content-type"].startswith("application/x-ndjson")
    items = _lines(response)
    assert items[0]["type"] == "run" and items[-1]["status"] == "done"
    assert [i["event"]["type"] for i in items if i["type"] == "event"] == [
        "DECISION",
        "TOOL",
        "OBSERVATION",
        "DECISION",
        "CHECK",
        "FINAL",
    ]

    run_id = items[0]["run_id"]
    stored = agent_client.get(f"/api/v1/runs/{run_id}").json()
    assert len(stored["events"]) == 6 and stored["metrics"]["llm_calls"] == 3
    session = agent_client.get("/api/v1/sessions/sess-1").json()
    assert session["case_id"] == "aaaaaaaaaaaa000000000001"
    metrics = agent_client.get("/api/v1/metrics").json()
    assert metrics["by_mode"]["single"]["runs"] == 1 and metrics["cost"].startswith(
        "non applicable"
    )


def test_export_waits_for_confirmation(agent_client: TestClient, settings: Settings) -> None:
    run_id = _lines(
        agent_client.post(
            "/api/v1/runs", json={"session_id": "sess-2", "question": "Faute grave ?"}
        )
    )[0]["run_id"]
    destination = str(settings.data_dir / "exports")

    pending = agent_client.post(
        f"/api/v1/runs/{run_id}/export", json={"destination": destination}
    ).json()
    assert not Path(destination).exists()  # rien n'est écrit avant la confirmation

    done = agent_client.post(
        f"/api/v1/approvals/{pending['approval_id']}", json={"decision": "approve"}
    ).json()
    assert done["status"] == "exported" and Path(done["path"]).exists()
    assert "[P1]" in done["content"]
    again = agent_client.post(
        f"/api/v1/approvals/{pending['approval_id']}", json={"decision": "approve"}
    )
    assert again.status_code == 409  # une décision ne se rejoue pas
    events = agent_client.get(f"/api/v1/runs/{run_id}").json()["events"]
    assert [e["summary"][:30] for e in events if e["type"] == "HUMAN"] == [
        "Validation humaine demandée : ",
        "Décision humaine : confirmée —",
    ]


def test_rejected_or_expired_export_writes_nothing(
    agent_client: TestClient, settings: Settings
) -> None:
    run_id = _lines(
        agent_client.post(
            "/api/v1/runs", json={"session_id": "sess-3", "question": "Faute grave ?"}
        )
    )[0]["run_id"]
    destination = str(settings.data_dir / "exports")
    container = agent_client.app.state.container  # type: ignore[attr-defined]

    first = agent_client.post(
        f"/api/v1/runs/{run_id}/export", json={"destination": destination}
    ).json()
    assert (
        agent_client.post(
            f"/api/v1/approvals/{first['approval_id']}", json={"decision": "reject"}
        ).json()["status"]
        == "rejected"
    )

    second = agent_client.post(
        f"/api/v1/runs/{run_id}/export", json={"destination": destination}
    ).json()
    container.runs._conn.execute(
        "UPDATE approvals SET created_at = ? WHERE approval_id = ?",
        (time.time() - 3600, second["approval_id"]),
    )
    expired = agent_client.post(
        f"/api/v1/approvals/{second['approval_id']}", json={"decision": "approve"}
    )
    assert expired.status_code == 410
    assert not Path(destination).exists()


def test_ndjson_lines_survive_unicode_line_separators() -> None:
    from jurirag.interfaces.http.routers.agent import ndjson_line

    line = ndjson_line({"text": "alinéa 1 alinéa 2 fin\u0085"})
    assert line.count(b"\n") == 1 and line.endswith(b"\n")
    assert line.decode().splitlines() == [
        line.decode().rstrip("\n")
    ]  # une seule ligne, même pour splitlines
    assert json.loads(line)["text"] == "alinéa 1 alinéa 2 fin\u0085"
