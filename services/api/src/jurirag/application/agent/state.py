"""État partagé du graphe.

Tout est sérialisable en JSON : l'état est sauvegardé après chaque nœud par le checkpointer
(mémoire de session, reprise après une validation humaine). Les clés « de session »
survivent d'une question à l'autre ; les clés « de run » sont remises à zéro par `start`.
"""

from typing import Any, TypedDict

SESSION_KEYS = ("session_case_id", "memory")


class AgentState(TypedDict, total=False):
    # --- entrée du run ---
    run_id: str
    question: str
    mode: str  # « single » | « multi »
    selected_case_id: str | None  # affaire sélectionnée dans l'interface
    # --- mémoire de session ---
    session_case_id: str | None  # affaire en cours de consultation
    memory: list[dict[str, Any]]  # derniers échanges : question, réponse courte, affaire
    memory_updated_at: float
    # --- état du run ---
    messages: list[dict[str, Any]]  # contexte de l'agent (ChatMessage sérialisés)
    evidence: dict[str, Any]  # EvidenceRegistry sérialisé : passages réellement montrés
    read_cases: list[str]
    queries: list[str]  # requêtes déjà jouées (normalisées) : évite les répétitions
    tool_history: list[dict[str, Any]]
    iteration: int
    max_iterations: int
    budget_extended: bool
    pending_calls: list[dict[str, Any]]
    draft: str | None
    verifier: dict[str, Any] | None
    verify_count: int
    research_brief: str | None  # mode multi : consigne du superviseur au chercheur
    research_report: str | None  # mode multi : dernier compte rendu du chercheur
    research_rounds: int  # mode multi : délégations au chercheur dans ce run
    pending_approval: dict[str, Any] | None  # demande de validation humaine en attente
    partial: bool  # réponse réduite aux seules affirmations vérifiées
    warning: str | None  # avertissement joint à la réponse (sources contradictoires)
    final: dict[str, Any] | None
    stop_reason: str | None
    metrics: dict[str, Any]
    step: int
    started_at: float
