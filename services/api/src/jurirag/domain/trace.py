"""Trace opérationnelle d'un run et métriques."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    # Les cinq types de base de la trace…
    DECISION = "DECISION"
    TOOL = "TOOL"
    OBSERVATION = "OBSERVATION"
    CHECK = "CHECK"
    FINAL = "FINAL"
    # … et deux types pour les erreurs et la validation humaine.
    ERROR = "ERROR"  # erreur d'outil ou de modèle
    HUMAN = "HUMAN"  # demande et décision de validation humaine


class StopReason(StrEnum):
    ANSWERED = "answered"
    ABSTAINED = "abstained"  # preuves restées insuffisantes
    MAX_ITERATIONS = "max_iterations"
    ERROR = "error"  # erreur non récupérable
    HUMAN_REJECTED = "human_rejected"
    HUMAN_TIMEOUT = "human_timeout"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class TraceEvent(BaseModel):
    run_id: str
    step: int
    type: EventType
    agent: str  # « agent », « superviseur », « chercheur », « vérificateur »
    summary: str  # une ligne lisible : justification opérationnelle courte, pas de CoT
    data: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = None
    at: str = Field(default_factory=_now)


class RunMetrics(BaseModel):
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_latency_ms: float = 0.0
    tool_calls: dict[str, int] = Field(default_factory=dict)
    tool_latency_ms: float = 0.0
    iterations: int = 0
    searches: int = 0
    errors: list[str] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    verifier_status: str | None = None
    stop_reason: StopReason | None = None
    # Coût monétaire : non applicable à un modèle local ; aucune valeur n'est inventée.
    cost: str = "non applicable (modèle local)"
