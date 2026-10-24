"""Socle RAG : recherche d'affaires, lecture, résumé, question-réponse (RAG statique)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from jurirag.application.rag import CaseSummary, StaticAnswer
from jurirag.domain.models import ZONE_LABELS, RetrievalMethod
from jurirag.interfaces.http.deps import ContainerDep, require_index

router = APIRouter(prefix="/api/v1", tags=["affaires"])


@router.get("/cases/search")
async def search_cases(
    container: ContainerDep,
    q: str = Query(min_length=2, max_length=300, description="Mots-clés ou question"),
    k: int = Query(10, ge=1, le=30),
    method: RetrievalMethod | None = None,
) -> dict[str, Any]:
    index = require_index(container)
    hits = await index.retriever.search(q, k=k * 4, method=method)
    results: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    for hit in hits:
        case_id = hit.passage.case_id
        if case_id in seen:
            if len(seen[case_id]["passages"]) < 3:
                seen[case_id]["passages"].append(
                    {
                        "passage_id": hit.passage.passage_id,
                        "zone": hit.passage.zone.value,
                        "text": hit.passage.text,
                    }
                )
            continue
        if len(results) == k:
            continue
        meta = index.store.get_meta(case_id)
        if meta is None:
            continue
        item = {
            "rank": len(results) + 1,
            "score": hit.score,
            "meta": meta.model_dump(mode="json"),
            "title": meta.title(),
            "passages": [
                {
                    "passage_id": hit.passage.passage_id,
                    "zone": hit.passage.zone.value,
                    "text": hit.passage.text,
                }
            ],
        }
        seen[case_id] = item
        results.append(item)
    return {
        "query": q,
        "method": (method or index.retriever.default_method).value,
        "results": results,
        "note": "Le score sert au classement ; ce n'est pas une preuve juridique.",
    }


@router.get("/cases/{case_id}")
async def get_case(case_id: str, container: ContainerDep) -> dict[str, Any]:
    index = require_index(container)
    case = index.store.get_case(case_id)
    if case is None:
        raise HTTPException(404, f"Décision inconnue : {case_id}")
    passages = index.store.passages_of(case_id)
    return {
        "meta": case.meta.model_dump(mode="json"),
        "title": case.meta.title(),
        "zones": [
            {"zone": z.zone.value, "label": ZONE_LABELS[z.zone], "text": case.text[z.start : z.end]}
            for z in case.zones
        ],
        "passages": [p.model_dump(mode="json") for p in passages],
    }


@router.post("/cases/{case_id}/summary")
async def summarize_case(case_id: str, container: ContainerDep) -> CaseSummary:
    require_index(container)
    assert container.rag is not None
    return await container.rag.summarize(case_id)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    case_id: str | None = None
    k: int = Field(5, ge=1, le=10)
    verify: bool = True


@router.post("/rag/ask")
async def ask_static(body: AskRequest, container: ContainerDep) -> StaticAnswer:
    """RAG statique : une recherche, un prompt, une réponse citée (vérifiée pour mesure)."""
    require_index(container)
    assert container.rag is not None
    return await container.rag.ask(
        body.question, k=body.k, case_id=body.case_id, verify=body.verify
    )
