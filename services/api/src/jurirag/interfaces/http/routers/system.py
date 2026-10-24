"""Santé du système et observabilité."""

from typing import Any

from fastapi import APIRouter, HTTPException

from jurirag.domain.errors import LLMError
from jurirag.interfaces.http.deps import ContainerDep

router = APIRouter(tags=["système"])


@router.get("/health")
async def health(container: ContainerDep) -> dict[str, Any]:
    """Ollama joignable ? modèles installés ? index construit ? — vérifié avant toute requête."""
    settings = container.settings
    ollama: dict[str, Any] = {"url": settings.ollama_base_url}
    try:
        models = await container.llm.list_models()
        ollama.update(reachable=True, models=models)
    except LLMError as exc:
        ollama.update(reachable=False, error=str(exc), models=[])
    installed = set(ollama["models"])
    embed_model = (
        container.index.manifest.get("embed_model") if container.index else None
    ) or settings.ollama_embed_model
    checks = {
        "ollama": ollama["reachable"],
        "generation_model": settings.ollama_model in installed,
        "embedding_model": embed_model in installed,
        "index": container.index is not None,
    }
    problems = []
    if not checks["ollama"]:
        problems.append(
            "Ollama n'est pas démarré : lancer `ollama serve` (ou l'application Ollama)."
        )
    else:
        if not checks["generation_model"]:
            problems.append(f"Modèle absent : `ollama pull {settings.ollama_model}`.")
        if not checks["embedding_model"]:
            problems.append(f"Modèle d'embedding absent : `ollama pull {embed_model}`.")
    if not checks["index"]:
        problems.append(container.index_error or "Index absent : `make index`.")
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "checks": checks,
        "problems": problems,
        "ollama": ollama,
        "generation_model": settings.ollama_model,
        "embedding_model": embed_model,
        "index": container.index.manifest if container.index else None,
        "agent": {
            "max_iterations": settings.agent_max_iterations,
            "hitl_timeout_s": settings.hitl_timeout_s,
            "memory_ttl_s": settings.memory_ttl_s,
            "retrieval_method": settings.retrieval_method.value,
            "params": settings.generation_params().model_dump(),
            "think_decide": settings.think_decide,
            "judge_temperature": settings.judge_temperature,
        },
    }


@router.get("/api/v1/runs")
async def list_runs(container: ContainerDep, limit: int = 100) -> list[dict[str, Any]]:
    return container.runs.list_runs(limit)


@router.get("/api/v1/runs/{run_id}")
async def get_run(run_id: str, container: ContainerDep) -> dict[str, Any]:
    run = container.runs.get_run(run_id)
    if run is None:
        raise HTTPException(404, "Run inconnu")
    return run


@router.get("/api/v1/metrics")
async def metrics(container: ContainerDep, limit: int = 500) -> dict[str, Any]:
    """Agrégats réels sur les runs terminés, par mode. Aucun coût monétaire inventé."""
    runs = [r for r in container.runs.list_runs(limit) if r.get("metrics")]
    by_mode: dict[str, dict[str, Any]] = {}
    for run in runs:
        m = run["metrics"]
        agg = by_mode.setdefault(
            run["mode"],
            {
                "runs": 0,
                "llm_calls": 0,
                "tool_calls": 0,
                "latency_ms": 0.0,
                "iterations": 0,
                "tokens": 0,
                "status": {},
                "stop": {},
            },
        )
        agg["runs"] += 1
        agg["llm_calls"] += m["llm_calls"]
        agg["tool_calls"] += sum(m["tool_calls"].values())
        agg["latency_ms"] += m["total_latency_ms"]
        agg["iterations"] += m["iterations"]
        agg["tokens"] += m["prompt_tokens"] + m["completion_tokens"]
        agg["status"][m.get("verifier_status") or "—"] = (
            agg["status"].get(m.get("verifier_status") or "—", 0) + 1
        )
        agg["stop"][m.get("stop_reason") or "—"] = (
            agg["stop"].get(m.get("stop_reason") or "—", 0) + 1
        )
    for agg in by_mode.values():
        n = agg["runs"]
        for key in ("llm_calls", "tool_calls", "latency_ms", "iterations", "tokens"):
            agg[f"avg_{key}"] = round(agg[key] / n, 1)
    return {"runs": len(runs), "by_mode": by_mode, "cost": "non applicable (modèle local)"}
