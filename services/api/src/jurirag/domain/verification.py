"""Résultat du vérificateur de preuves."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimVerdict(StrEnum):
    SUPPORTS = "supports"  # le passage cité établit l'affirmation
    CONTRADICTS = "contradicts"  # le passage cité dit le contraire
    NOT_ENOUGH_INFO = "not_enough_info"  # le passage ne permet pas de conclure


class VerifierStatus(StrEnum):
    # Toutes les affirmations sont soutenues par des passages réellement lus.
    SUFFICIENT = "sufficient"
    # Pas de preuve, citation absente ou inventée, ou affirmation non établie.
    INSUFFICIENT = "insufficient"
    # Au moins une affirmation est contredite par un passage cité.
    CONTRADICTORY = "contradictory"


class NextAction(StrEnum):
    ANSWER = "answer"
    SEARCH_AGAIN = "search_again"
    READ_CASE = "read_case"
    ABSTAIN = "abstain"
    ASK_HUMAN = "ask_human"


class ClaimCheck(BaseModel):
    """Une affirmation de la réponse candidate et son contrôle."""

    text: str
    citations: list[str] = Field(default_factory=list)  # passage_id cités
    verdict: ClaimVerdict = ClaimVerdict.NOT_ENOUGH_INFO
    # Règles déterministes violées (citation absente, citation inventée, date absente…).
    rule_failures: list[str] = Field(default_factory=list)
    reason: str = ""


class VerifierReport(BaseModel):
    status: VerifierStatus
    justification: str
    claims: list[ClaimCheck] = Field(default_factory=list)
    unverified_claims: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)  # passage_id effectivement disponibles
    next_action: NextAction
    llm_judge_used: bool = False
