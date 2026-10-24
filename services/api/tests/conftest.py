"""Doublures partagées : corpus en mémoire, retriever lexical naïf, LLM scripté."""

from collections.abc import Sequence
from typing import Any

import pytest

from jurirag.application.chunking import chunk_case
from jurirag.domain.llm import ChatMessage, GenerationParams, LLMResponse, ToolCall, ToolSpec
from jurirag.domain.models import (
    Case,
    CaseMeta,
    Passage,
    PassageHit,
    Provenance,
    RetrievalMethod,
    Zone,
    ZoneSpan,
)

PROVENANCE = Provenance(
    dataset="antoinejeannot/jurisprudence", revision="test", split="cour_de_cassation"
)


def make_case(case_id: str, expose: str, motivations: str, dispositif: str, **meta: Any) -> Case:
    parts = [expose, motivations, dispositif]
    zones, cursor = [], 0
    for zone, part in zip((Zone.EXPOSE, Zone.MOTIVATIONS, Zone.DISPOSITIF), parts, strict=True):
        zones.append(ZoneSpan(zone=zone, start=cursor, end=cursor + len(part)))
        cursor += len(part) + 2
    meta.setdefault("chamber", "Chambre sociale")
    meta.setdefault("decision_date", "2023-06-01")
    return Case(
        meta=CaseMeta(
            case_id=case_id, jurisdiction="Cour de cassation", provenance=PROVENANCE, **meta
        ),
        text="\n\n".join(parts),
        zones=zones,
    )


CASES = [
    make_case(
        "aaaaaaaaaaaa000000000001",
        "Faits et procédure. M. X, salarié, a été licencié pour faute grave le 3 mars 2019.",
        "Réponse de la Cour. La cour d'appel a retenu que l'abandon de poste constituait une faute grave.",
        "PAR CES MOTIFS, la Cour REJETTE le pourvoi.",
        solution="Rejet",
        number="21-10.001",
        themes=["licenciement", "faute grave"],
    ),
    make_case(
        "bbbbbbbbbbbb000000000002",
        "Faits et procédure. La société Y a donné à bail commercial un local à la société Z.",
        "Réponse de la Cour. Vu l'article L. 145-41 du code de commerce, le commandement était nul.",
        "PAR CES MOTIFS, la Cour CASSE ET ANNULE l'arrêt rendu le 12 mai 2021.",
        solution="Cassation",
        number="21-20.002",
        themes=["bail commercial", "clause résolutoire"],
    ),
]


class MemoryCases:
    """CaseRepository en mémoire."""

    def __init__(self, cases: Sequence[Case]) -> None:
        self.cases = {c.meta.case_id: c for c in cases}
        self.passages = {c.meta.case_id: chunk_case(c) for c in cases}

    def get_case(self, case_id: str) -> Case | None:
        return self.cases.get(case_id)

    def get_meta(self, case_id: str) -> CaseMeta | None:
        case = self.cases.get(case_id)
        return case.meta if case else None

    def passages_of(self, case_id: str) -> list[Passage]:
        return list(self.passages.get(case_id, []))

    def get_passages(self, passage_ids: Sequence[str]) -> list[Passage]:
        every = {p.passage_id: p for ps in self.passages.values() for p in ps}
        return [every[i] for i in passage_ids if i in every]

    def count_cases(self) -> int:
        return len(self.cases)

    def count_passages(self) -> int:
        return sum(len(p) for p in self.passages.values())


def _overlap(query: str, text: str) -> int:
    words = {w.lower().strip(".,;:'") for w in query.split() if len(w) > 3}
    return sum(1 for w in words if w in text.lower())


class WordRetriever:
    """Retriever par recouvrement de mots : suffit à tester la logique de contrôle."""

    def __init__(self, cases: MemoryCases, fail: Exception | None = None) -> None:
        self._cases = cases
        self.fail = fail
        self.queries: list[str] = []

    @property
    def available_methods(self) -> list[RetrievalMethod]:
        return [RetrievalMethod.BM25]

    async def search(
        self, query: str, k: int, method: RetrievalMethod | None = None
    ) -> list[PassageHit]:
        if self.fail:
            raise self.fail
        self.queries.append(query)
        scored = [(p, _overlap(query, p.text)) for ps in self._cases.passages.values() for p in ps]
        scored = sorted((s for s in scored if s[1] > 0), key=lambda s: -s[1])[:k]
        return [PassageHit(passage=p, score=float(s), rank=i) for i, (p, s) in enumerate(scored, 1)]

    async def search_in_case(self, query: str, case_id: str, k: int) -> list[PassageHit]:
        scored = sorted(
            ((p, _overlap(query, p.text)) for p in self._cases.passages.get(case_id, [])),
            key=lambda s: -s[1],
        )[:k]
        return [PassageHit(passage=p, score=float(s), rank=i) for i, (p, s) in enumerate(scored, 1)]


class ScriptedLLM:
    """LLM factice : rejoue des réponses préparées (texte et/ou appels d'outils)."""

    def __init__(self, script: Sequence[LLMResponse | Exception]) -> None:
        self._script = list(script)
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams,
        tools: Sequence[ToolSpec] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {
                "messages": list(messages),
                "tools": tools,
                "schema": response_schema,
                "params": params,
            }
        )
        if not self._script:
            raise AssertionError("ScriptedLLM : plus de réponse préparée")
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def list_models(self) -> list[str]:
        return ["qwen3.5:9b", "qwen3-embedding:0.6b"]


def reply(content: str = "", *calls: tuple[str, dict[str, Any]]) -> LLMResponse:
    return LLMResponse(
        content=content,
        tool_calls=[ToolCall(name=n, arguments=a) for n, a in calls],
        latency_ms=5.0,
        model="qwen3.5:9b",
        prompt_tokens=100,
        completion_tokens=20,
    )


@pytest.fixture
def cases() -> MemoryCases:
    return MemoryCases(CASES)


@pytest.fixture
def retriever(cases: MemoryCases) -> WordRetriever:
    return WordRetriever(cases)


class MemoryRunStore:
    def __init__(self) -> None:
        self.events: list[Any] = []
        self.runs: dict[str, dict[str, Any]] = {}

    def save_event(self, event: Any) -> None:
        self.events.append(event)

    def start_run(self, run_id: str, session_id: str, question: str, mode: str, model: str) -> None:
        self.runs[run_id] = {"session_id": session_id, "question": question, "mode": mode}

    def finish_run(self, run_id: str, metrics: Any, answer: str | None) -> None:
        self.runs[run_id].update(metrics=metrics, answer=answer)

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self.runs.values())[:limit]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.runs.get(run_id)
