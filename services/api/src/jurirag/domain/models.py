"""Entités métier : décisions, passages, résultats de recherche.

Couche la plus interne : aucune dépendance vers l'API, le LLM, l'index ou le dataset.
pydantic est le seul import tiers (validation et sérialisation des valeurs).
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Zone(StrEnum):
    """Sections d'un arrêt, telles que délimitées par le champ `zones` du dataset."""

    INTRODUCTION = "introduction"
    EXPOSE = "expose"
    MOYENS = "moyens"
    MOTIVATIONS = "motivations"
    DISPOSITIF = "dispositif"
    ANNEXES = "annexes"
    # Texte sans zonage exploitable : découpage récursif de repli.
    TEXTE = "texte"


ZONE_LABELS: dict[Zone, str] = {
    Zone.INTRODUCTION: "Introduction",
    Zone.EXPOSE: "Exposé du litige",
    Zone.MOYENS: "Moyens",
    Zone.MOTIVATIONS: "Motivations",
    Zone.DISPOSITIF: "Dispositif",
    Zone.ANNEXES: "Annexes",
    Zone.TEXTE: "Texte",
}


class Provenance(BaseModel):
    """D'où vient une décision : permet de citer et de reconstruire l'index."""

    model_config = ConfigDict(frozen=True)

    source: str = "corpus"  # « corpus » (index local) ; une source externe aurait un autre nom
    dataset: str
    revision: str
    split: str
    url: str | None = None


class CaseMeta(BaseModel):
    """Métadonnées d'une décision (sans le texte)."""

    case_id: str
    jurisdiction: str
    chamber: str | None = None
    formation: str | None = None
    decision_type: str | None = None
    decision_date: str | None = None
    number: str | None = None
    ecli: str | None = None
    solution: str | None = None
    publication: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    summary: str | None = None
    visa: list[str] = Field(default_factory=list)
    contested: str | None = None
    provenance: Provenance

    def title(self) -> str:
        parts = [self.jurisdiction]
        if self.chamber:
            parts.append(self.chamber)
        if self.decision_date:
            parts.append(self.decision_date)
        if self.number:
            parts.append(f"n° {self.number}")
        return " · ".join(parts)


class ZoneSpan(BaseModel):
    model_config = ConfigDict(frozen=True)

    zone: Zone
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class Case(BaseModel):
    """Décision complète : métadonnées, texte et zonage."""

    meta: CaseMeta
    text: str
    zones: list[ZoneSpan] = Field(default_factory=list)

    def zone_text(self, zone: Zone) -> str:
        spans = [s for s in self.zones if s.zone == zone]
        return "\n".join(self.text[s.start : s.end].strip() for s in spans).strip()


class Passage(BaseModel):
    """Extrait indexé d'une décision. `passage_id` sert de référence de citation."""

    model_config = ConfigDict(frozen=True)

    passage_id: str  # « {case_id}#{zone}-{ordinal} »
    case_id: str
    zone: Zone
    ordinal: int = Field(ge=0)
    start: int = Field(ge=0)  # offsets dans `Case.text` : provenance exacte de l'extrait
    end: int = Field(ge=0)
    text: str


class RetrievalMethod(StrEnum):
    BM25 = "bm25"
    DENSE = "dense"
    HYBRID = "hybrid"


class PassageHit(BaseModel):
    passage: Passage
    score: float
    rank: int = Field(ge=1)


class CaseHit(BaseModel):
    """Une décision retrouvée, avec les passages qui l'ont fait remonter."""

    meta: CaseMeta
    score: float  # score de classement (BM25, cosinus ou RRF) : jamais une preuve
    rank: int = Field(ge=1)
    passages: list[PassageHit]
