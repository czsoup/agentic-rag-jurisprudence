"""Logique de contrôle de la boucle agentique, avec un LLM scripté (aucun appel réel)."""

import json
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from jurirag.application.agent.graph import AgentConfig, AgentGraph
from jurirag.application.agent.runner import AgentRunner
from jurirag.application.agent.tools import CaseTools, ToolExecutor
from jurirag.domain.errors import LLMUnavailableError
from jurirag.domain.llm import GenerationParams
from tests.conftest import MemoryCases, MemoryRunStore, ScriptedLLM, WordRetriever, reply

PARAMS = GenerationParams(
    model="qwen3.5:9b", temperature=0.1, seed=42, top_p=0.9, num_predict=512, num_ctx=8192
)
LICENCIEMENT = "aaaaaaaaaaaa000000000001"
BAIL = "bbbbbbbbbbbb000000000002"


def judge(*verdicts: str) -> Any:
    return reply(
        json.dumps(
            {
                "verdicts": [
                    {"claim": i, "verdict": v, "reason": "r"} for i, v in enumerate(verdicts, 1)
                ],
                "addresses_question": True,
                "relevance_reason": "r",
            }
        )
    )


def make_runner(
    llm: ScriptedLLM, cases: MemoryCases, retriever: WordRetriever, **config: Any
) -> tuple[AgentRunner, MemoryRunStore]:
    cfg = AgentConfig(params=PARAMS, judge_params=PARAMS, **config)
    graph = AgentGraph(llm, ToolExecutor(CaseTools(retriever, cases)), cases, cfg)
    saver = InMemorySaver()
    store = MemoryRunStore()
    runner = AgentRunner(
        {"single": graph.builder().compile(checkpointer=saver)},
        saver,
        store,
        "qwen3.5:9b",
        hitl_timeout_s=300,
    )
    return runner, store


async def collect(stream: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events, status = [], {}
    async for item in stream:
        if item["type"] == "event":
            events.append(item["event"])
        elif item["type"] == "status":
            status = item
    return events, status


def types(events: list[dict[str, Any]]) -> list[str]:
    return [e["type"] for e in events]


async def test_scenario_1_single_search_then_verified_answer(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply(
                "", ("search_cases", {"query": "licenciement faute grave abandon de poste", "k": 3})
            ),
            reply(
                "La Cour rejette le pourvoi formé par le salarié licencié pour faute grave [P1]."
            ),
            judge("supports"),
        ]
    )
    runner, store = make_runner(llm, cases, retriever)

    events, status = await collect(runner.run("s1", "Abandon de poste et faute grave ?"))

    assert types(events) == ["DECISION", "TOOL", "OBSERVATION", "DECISION", "CHECK", "FINAL"]
    final = status["final"]
    assert status["status"] == "done" and final["status"] == "answered"
    assert (
        final["sources"][0]["case_id"] == LICENCIEMENT and final["sources"][0]["origin"] == "corpus"
    )
    metrics = status["metrics"]
    assert (
        metrics["llm_calls"] == 3
        and metrics["tool_calls"] == {"search_cases": 1}
        and metrics["searches"] == 1
    )
    assert metrics["stop_reason"] == "answered" and metrics["cost"].startswith("non applicable")
    assert len(store.events) == len(events)  # chaque événement est persisté


async def test_scenario_2_search_then_read_case(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "bail commercial commandement"})),
            reply("", ("read_case", {"case_id": BAIL, "focus": "commandement clause résolutoire"})),
            reply(
                "Le commandement était nul au regard de l'article L. 145-41 du code de commerce [P2]. "
                "La Cour casse et annule l'arrêt rendu le 12 mai 2021 [P3]."
            ),
            judge("supports", "supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    events, status = await collect(runner.run("s2", "Que décide la Cour sur le commandement ?"))

    tools = [e["data"]["name"] for e in events if e["type"] == "TOOL"]
    assert tools == ["search_cases", "read_case"]
    assert status["final"]["verifier_status"] == "sufficient"
    assert {s["zone"] for s in status["final"]["sources"]} >= {"dispositif"}


async def test_scenario_3_insufficient_then_reformulation_then_abstention(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "brevet contrefaçon logiciel"})),
            reply("", ("search_cases", {"query": "propriété intellectuelle invention"})),
            reply("Le corpus ne permet pas de répondre : aucune décision trouvée sur ce point."),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever, hitl_enabled=False)

    events, status = await collect(runner.run("s3", "Un logiciel est-il brevetable ?"))

    assert [e["data"]["arguments"]["query"] for e in events if e["type"] == "TOOL"] == [
        "brevet contrefaçon logiciel",
        "propriété intellectuelle invention",
    ]
    assert status["final"]["status"] == "abstained"
    assert status["final"]["sources"] == []


async def test_unsourced_answer_triggers_new_search_with_feedback(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "licenciement faute grave"})),
            reply("Le salarié a obtenu 20 000 euros de dommages et intérêts."),  # non sourcé
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("La Cour rejette le pourvoi [P3]."),
            judge("supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    events, status = await collect(runner.run("s4", "Quelle indemnité ?"))

    checks = [e for e in events if e["type"] == "CHECK"]
    assert [c["data"]["status"] for c in checks] == ["insufficient", "sufficient"]
    feedback = (
        llm.calls[2]["messages"][-1].content if llm.calls[2]["messages"][-1].role == "user" else ""
    )
    assert "Vérification" in json.dumps(
        [m.content for m in llm.calls[2]["messages"]], ensure_ascii=False
    )
    assert status["final"]["status"] == "answered" and feedback is not None


async def test_iteration_limit_is_enforced(cases: MemoryCases, retriever: WordRetriever) -> None:
    queries = [
        "licenciement",
        "faute grave salarié",
        "abandon de poste",
        "rupture contrat travail",
        "pourvoi rejet salarié",
        "jamais exécutée",
    ]
    llm = ScriptedLLM([reply("", ("search_cases", {"query": q})) for q in queries])
    runner, _ = make_runner(llm, cases, retriever, max_iterations=3, hitl_enabled=False)

    events, status = await collect(runner.run("s5", "Question sans fin"))

    assert sum(1 for e in events if e["type"] == "TOOL") == 3
    assert status["final"]["stop_reason"] == "max_iterations"
    assert len(llm.calls) == 3


async def test_repeated_query_is_not_executed(cases: MemoryCases, retriever: WordRetriever) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "faute grave licenciement"})),
            reply("", ("search_cases", {"query": "licenciement faute grave"})),  # mêmes mots
            reply("La Cour rejette le pourvoi formé contre l'arrêt [P1]."),
            judge("supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    events, status = await collect(runner.run("s6", "Faute grave ?"))

    assert len(retriever.queries) == 1
    assert any(e["type"] == "ERROR" and "répétée" in e["summary"] for e in events)
    assert status["metrics"]["searches"] == 1


async def test_ollama_down_stops_cleanly(cases: MemoryCases, retriever: WordRetriever) -> None:
    runner, _ = make_runner(
        ScriptedLLM([LLMUnavailableError("Ollama injoignable")]), cases, retriever
    )

    events, status = await collect(runner.run("s7", "Question"))

    assert types(events) == ["ERROR", "FINAL"]
    assert status["final"]["status"] == "error" and status["final"]["stop_reason"] == "error"


async def test_malformed_tool_call_executes_nothing(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"__raw__": "licenciement"})),
            reply("", ("rm_rf", {"path": "/"})),
            reply("Le corpus ne permet pas de répondre."),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever, hitl_enabled=False)

    events, status = await collect(runner.run("s8", "Question"))

    assert retriever.queries == []
    assert [e["data"]["error"] for e in events if e["type"] == "ERROR"] == [
        "invalid_arguments",
        "unknown_tool",
    ]
    assert status["final"]["status"] == "abstained"


async def test_memory_keeps_the_case_between_questions(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "licenciement faute grave"})),
            reply("La Cour rejette le pourvoi formé par le salarié [P1]."),
            judge("supports"),
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("La Cour rejette le pourvoi [P3]."),
            judge("supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    _, first = await collect(runner.run("mem", "Faute grave ?"))
    _, second = await collect(runner.run("mem", "Et quelle est la solution de cette affaire ?"))

    assert first["memory"]["case_id"] == LICENCIEMENT
    system = llm.calls[3]["messages"][0].content
    assert f"case_id={LICENCIEMENT}" in system and "Faute grave ?" in system
    assert [m["question"] for m in second["memory"]["turns"]] == [
        "Faute grave ?",
        "Et quelle est la solution de cette affaire ?",
    ]

    # Une autre session ne voit rien de cette mémoire.
    other = await runner.snapshot("autre-session")
    assert other["values"] == {}
    await runner.reset("mem")
    assert (await runner.snapshot("mem"))["values"] == {}


async def test_selecting_another_case_purges_memory(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply(
                "La Cour rejette le pourvoi formé [P1].",
            ),
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("La Cour rejette le pourvoi [P1]."),
            judge("supports"),
            reply("", ("read_case", {"case_id": BAIL})),
            reply(
                "La Cour casse et annule l'arrêt [P3]."
            ),  # les alias repartent de P1 à chaque run
            judge("supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    _, first = await collect(runner.run("sel", "Solution ?", selected_case_id=LICENCIEMENT))
    _, second = await collect(runner.run("sel", "Solution ?", selected_case_id=BAIL))

    assert first["memory"]["case_id"] == LICENCIEMENT
    assert second["memory"]["case_id"] == BAIL
    assert [m["case_id"] for m in second["memory"]["turns"]] == [BAIL]


@pytest.mark.parametrize(
    ("decision", "expected"), [("reject", "max_iterations"), ("approve", "answered")]
)
async def test_budget_extension_requires_human_approval(
    cases: MemoryCases, retriever: WordRetriever, decision: str, expected: str
) -> None:
    script = [reply("", ("search_cases", {"query": q})) for q in ["licenciement", "faute grave"]]
    script += [
        reply("", ("read_case", {"case_id": LICENCIEMENT})),
        reply("La Cour rejette le pourvoi [P3]."),
        judge("supports"),
    ]
    llm = ScriptedLLM(script)
    runner, _ = make_runner(llm, cases, retriever, max_iterations=2)

    events, status = await collect(runner.run("hitl", "Question"))
    assert status["status"] == "awaiting_approval" and status["approval"]["kind"] == "extend_budget"
    assert len(llm.calls) == 2  # bloqué : aucun appel tant que l'humain n'a pas répondu

    events, status = await collect(runner.resume("hitl", decision))
    assert events[0]["type"] == "HUMAN"
    assert status["final"]["stop_reason"] == expected


async def test_pending_approval_expires_when_a_new_question_arrives(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    script = [reply("", ("search_cases", {"query": q})) for q in ["licenciement", "faute grave"]]
    script += [
        reply("", ("search_cases", {"query": "bail commercial"})),
        reply("Le corpus ne permet pas de répondre."),
    ]
    llm = ScriptedLLM(script)
    runner, _ = make_runner(llm, cases, retriever, max_iterations=2)

    _, status = await collect(runner.run("exp", "Question"))
    assert status["status"] == "awaiting_approval"

    items = [i async for i in runner.run("exp", "Nouvelle question")]
    human = [i["event"] for i in items if i["type"] == "event" and i["event"]["type"] == "HUMAN"]
    assert human[0]["data"]["decision"] == "timeout"


async def test_contradiction_needs_approval_before_publication(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("read_case", {"case_id": LICENCIEMENT})),
            reply("La Cour casse l'arrêt et donne raison au salarié [P3]."),
            judge("contradicts"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    _, status = await collect(runner.run("ctr", "Qui gagne ?"))
    assert status["approval"]["kind"] == "publish_contradictory"

    _, status = await collect(runner.resume("ctr", "approve"))
    assert status["final"]["status"] == "answered"
    assert any("contredisent" in limit for limit in status["final"]["limits"])


async def test_premature_abstention_forces_reading_the_found_case(
    cases: MemoryCases, retriever: WordRetriever
) -> None:
    llm = ScriptedLLM(
        [
            reply("", ("search_cases", {"query": "licenciement faute grave abandon"})),
            reply(
                "La décision ne précise pas la date du licenciement dans l'extrait fourni [P1]."
            ),  # observé au banc
            reply("", ("read_case", {"case_id": LICENCIEMENT, "focus": "date du licenciement"})),
            reply("Le salarié a été licencié pour faute grave le 3 mars 2019 [P2]."),
            judge("supports"),
        ]
    )
    runner, _ = make_runner(llm, cases, retriever)

    events, status = await collect(runner.run("s9", "Quand le salarié a-t-il été licencié ?"))

    sent = " ".join(m.content for m in llm.calls[2]["messages"] if m.role == "user")
    assert f'read_case(case_id="{LICENCIEMENT}")' in sent
    assert any(
        e["type"] == "CHECK" and e["data"].get("guard") == "read_before_concluding" for e in events
    )
    assert len(llm.calls) == 5  # aucun appel au juge pour la réponse « ne précise pas »
    assert [e["data"]["name"] for e in events if e["type"] == "TOOL"] == [
        "search_cases",
        "read_case",
    ]
    assert status["final"]["status"] == "answered"
