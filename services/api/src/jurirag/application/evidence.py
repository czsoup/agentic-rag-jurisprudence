"""Registre des preuves d'un run : les passages réellement montrés au modèle.

Chaque passage reçoit un alias court (P1, P2…) au moment où un outil le renvoie. Le modèle
cite ces alias ; le code les traduit en références exactes (`passage_id`, offsets, décision).
Une citation dont l'alias n'est pas dans le registre est, par construction, inventée.
"""

import re

from pydantic import BaseModel, Field

from jurirag.domain.models import CaseMeta, Passage

CITATION = re.compile(r"\[(P\d+(?:\s*[,;]\s*P\d+)*)\]")


class EvidenceRegistry(BaseModel):
    passages: dict[str, Passage] = Field(default_factory=dict)  # alias → passage
    aliases: dict[str, str] = Field(default_factory=dict)  # passage_id → alias
    cases: dict[str, CaseMeta] = Field(default_factory=dict)  # case_id → métadonnées

    def add(self, passage: Passage, meta: CaseMeta | None = None) -> str:
        if passage.passage_id in self.aliases:
            return self.aliases[passage.passage_id]
        alias = f"P{len(self.passages) + 1}"
        self.passages[alias] = passage
        self.aliases[passage.passage_id] = alias
        if meta is not None:
            self.cases.setdefault(meta.case_id, meta)
        return alias

    def get(self, alias: str) -> Passage | None:
        return self.passages.get(alias)

    def __len__(self) -> int:
        return len(self.passages)


def extract_citations(text: str) -> list[str]:
    """Alias cités dans un texte, dans l'ordre, sans doublon : « [P1] », « [P2, P5] »."""
    found: list[str] = []
    for group in CITATION.findall(text):
        for alias in re.split(r"\s*[,;]\s*", group):
            if alias not in found:
                found.append(alias)
    return found
