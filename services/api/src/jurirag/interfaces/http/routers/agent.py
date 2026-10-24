"""Agentic RAG : runs diffusés en direct (NDJSON), validation humaine, mémoire, export."""

import json
import time
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from jurirag.application.agent.runner import AgentRunner
from jurirag.domain.errors import JuriragError
from jurirag.domain.trace import EventType, TraceEvent
from jurirag.interfaces.http.container import Container
from jurirag.interfaces.http.deps import ContainerDep, require_index

router = APIRouter(prefix="/api/v1", tags=["agent"])


def _runner(container: Container) -> AgentRunner:
    require_index(container)
    assert container.runner is not None
    return container.runner


# Séparateurs Unicode que `ensure_ascii=False` laisse passer et que beaucoup de lecteurs
# « ligne par ligne » (str.splitlines, httpx.iter_lines) prennent pour des fins de ligne.
# Observé sur des textes réels du corpus : une ligne NDJSON coupée en deux.
_LINE_BREAKERS = {"\u2028": "\\u2028", "\u2029": "\\u2029", "\u0085": "\\u0085"}


def ndjson_line(item: dict[str, Any]) -> bytes:
    line = json.dumps(item, ensure_ascii=False)
    for raw, escaped in _LINE_BREAKERS.items():
        line = line.replace(raw, escaped)
    return (line + "\n").encode()


async def _ndjson(stream: AsyncIterator[dict[str, Any]]) -> AsyncIterator[bytes]:
    """Une ligne JSON par événement, envoyée dès qu'il est émis (trace quasi directe)."""
    try:
        async for item in stream:
            yield ndjson_line(item)
    except JuriragError as exc:  # erreur imprévue : visible côté interface, pas un 500 muet
        yield ndjson_line({"type": "status", "status": "error", "error": str(exc)})


class RunRequest(BaseModel):
    session_id: str = Field(min_length=4, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    question: str = Field(min_length=3, max_length=1000)
    mode: Literal["single", "multi"] = "single"
    case_id: str | None = None  # affaire sélectionnée dans l'interface


@router.post("/runs")
async def start_run(body: RunRequest, container: ContainerDep) -> StreamingResponse:
    runner = _runner(container)
    stream = runner.run(body.session_id, body.question, body.mode, body.case_id)
    return StreamingResponse(_ndjson(stream), media_type="application/x-ndjson")


class ResumeRequest(BaseModel):
    decision: Literal["approve", "reject"]


@router.post("/sessions/{session_id}/resume")
async def resume_run(
    session_id: str, body: ResumeRequest, container: ContainerDep
) -> StreamingResponse:
    """Réponse humaine à une validation en attente ; au-delà du délai, elle compte comme expirée."""
    runner = _runner(container)
    return StreamingResponse(
        _ndjson(runner.resume(session_id, body.decision)), media_type="application/x-ndjson"
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, container: ContainerDep) -> dict[str, Any]:
    snapshot = await _runner(container).snapshot(session_id)
    values = snapshot["values"]
    return {
        "session_id": session_id,
        "case_id": values.get("session_case_id"),
        "memory": values.get("memory") or [],
        "memory_updated_at": values.get("memory_updated_at"),
        "ttl_s": container.settings.memory_ttl_s,
        "pending_approval": snapshot["pending"],
        "last_run_id": values.get("run_id"),
    }


@router.delete("/sessions/{session_id}")
async def reset_session(session_id: str, container: ContainerDep) -> dict[str, str]:
    await _runner(container).reset(session_id)
    return {"status": "reset", "session_id": session_id}


# --- Export du dossier (action sensible : validation humaine obligatoire) ---


class ExportRequest(BaseModel):
    destination: str = Field("data/exports", max_length=200)


@router.post("/runs/{run_id}/export")
async def request_export(
    run_id: str, body: ExportRequest, container: ContainerDep
) -> dict[str, Any]:
    """Demande d'export : rien n'est écrit tant que l'humain n'a pas confirmé."""
    run = container.runs.get_run(run_id)
    if run is None or not run.get("answer"):
        raise HTTPException(404, "Run inconnu ou sans réponse finale")
    approval_id = uuid.uuid4().hex[:12]
    payload = {"run_id": run_id, "destination": body.destination, "question": run["question"]}
    now = time.time()
    container.runs.create_approval(approval_id, "export", payload, now)
    _trace(
        container,
        run_id,
        "Validation humaine demandée : export du dossier hors de l'application.",
        {"approval_id": approval_id, **payload},
    )
    return {
        "approval_id": approval_id,
        "question": f"Exporter la réponse, les extraits cités et la trace vers « {body.destination} » ?",
        "expires_at": now + container.settings.hitl_timeout_s,
    }


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]


@router.post("/approvals/{approval_id}")
async def decide_approval(
    approval_id: str, body: ApprovalDecision, container: ContainerDep
) -> dict[str, Any]:
    approval = container.runs.get_approval(approval_id)
    if approval is None:
        raise HTTPException(404, "Demande de validation inconnue")
    if approval["decision"] is not None:
        raise HTTPException(409, f"Demande déjà traitée ({approval['decision']})")
    payload = approval["payload"]
    now = time.time()
    if now - approval["created_at"] > container.settings.hitl_timeout_s:
        container.runs.decide_approval(approval_id, "timeout", now)
        _trace(
            container,
            payload["run_id"],
            "Décision humaine : expirée — export annulé.",
            {"approval_id": approval_id, "decision": "timeout"},
        )
        raise HTTPException(410, "Délai de validation dépassé : export annulé")
    container.runs.decide_approval(approval_id, body.decision, now)
    if body.decision == "reject":
        _trace(
            container,
            payload["run_id"],
            "Décision humaine : refusée — rien n'a été exporté.",
            {"approval_id": approval_id, "decision": "reject"},
        )
        return {"status": "rejected"}

    run = container.runs.get_run(payload["run_id"])
    assert run is not None
    content = _export_markdown(run)
    directory = Path(payload["destination"])
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"dossier_{payload['run_id']}.md"
    path.write_text(content, encoding="utf-8")
    _trace(
        container,
        payload["run_id"],
        f"Décision humaine : confirmée — dossier exporté ({path}).",
        {"approval_id": approval_id, "decision": "approve", "path": str(path)},
    )
    return {"status": "exported", "path": str(path), "content": content}


def _trace(container: Container, run_id: str, summary: str, data: dict[str, Any]) -> None:
    run = container.runs.get_run(run_id)
    step = max((e["step"] for e in (run or {}).get("events", [])), default=0) + 1
    container.runs.save_event(
        TraceEvent(
            run_id=run_id,
            step=step,
            type=EventType.HUMAN,
            agent="utilisateur",
            summary=summary,
            data=data,
        )
    )


def _export_markdown(run: dict[str, Any]) -> str:
    final: dict[str, Any] = next(
        (e["data"] for e in reversed(run["events"]) if e["type"] == "FINAL"), {}
    )
    lines = [
        f"# Dossier — {run['question']}",
        "",
        f"Run `{run['run_id']}` · mode {run['mode']} · modèle {run['model']}",
        "",
        "## Réponse",
        "",
        final.get("answer", run.get("answer") or ""),
    ]
    if final.get("sources"):
        lines += ["", "## Passages cités", ""]
        for s in final["sources"]:
            lines += [
                f"**[{s['alias']}] {s['title']} — {s['zone_label']}** (`{s['passage_id']}`, source : {s['origin']})",
                "",
                f"> {' '.join(s['text'].split())}",
                "",
            ]
    if final.get("limits"):
        lines += ["## Limites", ""] + [f"- {limit}" for limit in final["limits"]]
    lines += ["", "## Trace", ""] + [
        f"{e['step']}. **{e['type']}** ({e['agent']}) — {e['summary']}" for e in run["events"]
    ]
    return "\n".join(lines) + "\n"
