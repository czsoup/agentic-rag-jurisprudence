"""Variante superviseur / chercheur / vérificateur, avec un LLM scripté."""

import json
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from jurirag.application.agent.graph import AgentConfig
from jurirag.application.agent.multi import MultiAgentGraph
from jurirag.application.agent.runner import AgentRunner
from jurirag.application.agent.tools import CaseTools, ToolExecutor
from tests.conftest import MemoryCases, MemoryRunStore, ScriptedLLM, WordRetriever, reply
from tests.unit.test_agent_graph import PARAMS, collect, judge

LICENCIEMENT = "aaaaaaaaaaaa000000000001"


def route(next_: str, brief: str = "", reason: str = "r") -> Any:
    return reply(json.dumps({"next": next_, "brief": brief, "reason": reason}))


def make(
    llm: ScriptedLLM, cases: MemoryCases, retriever: WordRetriever, **config: Any
) -> AgentRunner:
    cfg = AgentConfig(params=PARAMS, judge_params=PARAMS, **config)
    graph = MultiAgentGraph(llm, ToolExecutor(CaseTools(retriever, cases)), cases, cfg)
    saver = InMemorySaver()
    return AgentRunner(
        {"multi": graph.builder().compile(checkpointer=saver)}, saver, MemoryRunStore(), "m", 300
    )


async def test_supervisor_delegates_then_writes_then_verifier_validates(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            route("researcher", "décisions sur la faute grave pour abandon de poste"),
            reply("", ("search_cases", {"query": "abandon de poste faute grave"})),
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("Décision pertinente : P1, P4 (dispositif)."),
            route("write"),
            reply(
                "La Cour rejette le pourvoi formé par le salarié [P3]."
            ),  # dispositif = P3 (P1 déjà attribué)
            judge("supports"),
        ]
    )
    runner = make(llm, cases, retriever)

    events, status = await collect(runner.run("m1", "Abandon de poste ?", mode="multi"))

    agents = [e["agent"] for e in events]
    assert agents[0] == "superviseur" and "chercheur" in agents and "vérificateur" in agents
    assert status["final"]["status"] == "answered"
    assert status["metrics"]["tool_calls"] == {"search_cases": 1, "read_case": 1}
    assert status["metrics"]["llm_calls"] == 7


async def test_supervisor_cannot_write_without_evidence(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            route("write"),  # refusé : dossier vide
            reply("", ("search_cases", {"query": "bail commercial"})),
            reply("Passage P1."),
            route("write"),
            reply("Le commandement était nul selon la Cour [P1]."),
            judge("supports"),
        ]
    )
    runner = make(llm, cases, retriever)

    events, status = await collect(runner.run("m2", "Bail commercial ?", mode="multi"))

    first = events[0]
    assert first["data"]["action"] == "researcher" and "dossier vide" in first["summary"]
    assert status["final"]["status"] == "answered"


async def test_invalid_supervisor_output_falls_back_to_research(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("pas du json"),
            reply("", ("search_cases", {"query": "licenciement faute grave"})),
            reply("P1 utile."),
            route("stop"),
        ]
    )
    runner = make(llm, cases, retriever, hitl_enabled=False)

    events, status = await collect(runner.run("m3", "Question", mode="multi"))

    assert events[0]["data"]["action"] == "researcher"
    assert "superviseur : sortie invalide" in status["metrics"]["errors"]
    assert status["final"]["status"] == "abstained"


async def test_failed_check_returns_to_supervisor(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            route("researcher", "faute grave"),
            reply("", ("search_cases", {"query": "faute grave"})),
            reply("P1."),
            route("write"),
            reply(
                "Le salarié a reçu une indemnité de 5 000 euros [P1]."
            ),  # montant absent : règle R3
            judge("supports"),
            route("researcher", "lire la décision"),
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("P2 à P4."),
            route("write"),
            reply("La Cour rejette le pourvoi [P3]."),
            judge("supports"),
        ]
    )
    runner = make(llm, cases, retriever)

    events, status = await collect(runner.run("m4", "Indemnité ?", mode="multi"))

    checks = [e["data"]["status"] for e in events if e["type"] == "CHECK"]
    assert checks == ["insufficient", "sufficient"]
    assert status["final"]["status"] == "answered"


async def test_supervisor_cannot_keep_delegating_once_a_dossier_exists(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            route("researcher", "faute grave"),
            reply("", ("search_cases", {"query": "licenciement faute grave"})),
            reply("La réponse est dans [P1]."),
            route(
                "researcher", "chercher encore"
            ),  # v1 : relançait sans fin — désormais converti en rédaction
            reply("La Cour rejette le pourvoi formé par le salarié [P1]."),
            judge("supports"),
        ]
    )
    runner = make(llm, cases, retriever)

    events, status = await collect(runner.run("m5", "Faute grave ?", mode="multi"))

    second = [e for e in events if e["agent"] == "superviseur" and e["type"] == "DECISION"][1]
    assert second["data"]["action"] == "write" and "vérificateur" in second["summary"]
    assert status["final"]["status"] == "answered"
    supervisor_prompt = llm.calls[3]["messages"][1].content
    assert "COMPTE RENDU DU CHERCHEUR" in supervisor_prompt and "[P1]" in supervisor_prompt
