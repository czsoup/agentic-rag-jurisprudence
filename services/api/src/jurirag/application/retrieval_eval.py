"""Évaluation du retrieval au niveau des décisions.

Il n'existe pas de jeu annoté pour ce corpus. On construit des pseudo-requêtes à partir des
arrêts publiés au Bulletin, qui portent deux champs rédigés par la Cour :
- `summary` (sommaire) : son début sert de requête en langage naturel ;
- `themes` (titrage) : ses premiers mots-clés servent de requête par mots-clés.
La décision source est la réponse attendue. Biais connus, à rappeler avec les chiffres :
le sommaire paraphrase la motivation (favorable au lexical) ; d'autres décisions du corpus
peuvent être pertinentes sans être comptées ; seul le classement relatif des méthodes a du sens.
"""

import json
import random
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from jurirag.application.ports import LLMPort, RetrieverPort
from jurirag.domain.llm import ChatMessage, GenerationParams
from jurirag.domain.models import CaseMeta, RetrievalMethod

PARAPHRASE_SYSTEM = """Tu transformes le sommaire d'un arrêt de la Cour de cassation en la \
question qu'un justiciable ou un étudiant poserait pour retrouver cet arrêt. Écris UNE \
question en français courant, de 12 à 25 mots, sans numéro d'article, sans nom de partie, \
sans reprendre les expressions du sommaire : reformule avec tes propres mots. Réponds \
uniquement par la question."""


@dataclass(frozen=True)
class EvalQuery:
    kind: str  # « sommaire » | « thèmes »
    text: str
    case_id: str


@dataclass
class MethodScore:
    method: str
    kind: str
    n: int = 0
    hits: dict[int, int] = field(default_factory=lambda: {1: 0, 5: 0, 10: 0})
    reciprocal_ranks: float = 0.0
    latency_ms: float = 0.0

    def as_row(self) -> dict[str, float | str | int]:
        n = max(self.n, 1)
        return {
            "méthode": self.method,
            "requêtes": self.kind,
            "n": self.n,
            "Hit@1": round(self.hits[1] / n, 3),
            "Hit@5": round(self.hits[5] / n, 3),
            "Hit@10": round(self.hits[10] / n, 3),
            "MRR@10": round(self.reciprocal_ranks / n, 3),
            "latence moy. (ms)": round(self.latency_ms / n, 1),
        }


def build_queries(
    metas: list[CaseMeta], n: int, seed: int = 42, words: int = 30
) -> list[EvalQuery]:
    published = [m for m in metas if m.summary and m.themes]
    rng = random.Random(seed)
    sample = rng.sample(published, min(n, len(published)))
    queries = []
    for meta in sample:
        assert meta.summary is not None
        summary = re.sub(r"\s+", " ", meta.summary).strip()
        queries.append(EvalQuery("sommaire", " ".join(summary.split()[:words]), meta.case_id))
        queries.append(EvalQuery("thèmes", " ".join(meta.themes[:4]), meta.case_id))
    return queries


async def add_paraphrases(
    queries: list[EvalQuery],
    metas: dict[str, CaseMeta],
    llm: LLMPort,
    params: GenerationParams,
    cache: Path,
) -> list[EvalQuery]:
    """Ajoute une requête « question » par décision : sommaire reformulé par le LLM local.

    Réduit le biais lexical des requêtes « sommaire ». Les questions sont mises en cache
    (fichier JSON versionné) : l'évaluation reste reproductible sans rappeler le modèle.
    """
    cached: dict[str, str] = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    case_ids = list(dict.fromkeys(q.case_id for q in queries))
    for case_id in case_ids:
        if case_id in cached:
            continue
        summary = metas[case_id].summary or ""
        response = await llm.chat(
            [
                ChatMessage(role="system", content=PARAPHRASE_SYSTEM),
                ChatMessage(role="user", content=summary[:1500]),
            ],
            params,
        )
        cached[case_id] = " ".join(response.content.split()).strip('"« »')
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(cached, ensure_ascii=False, indent=1), encoding="utf-8")
    return queries + [EvalQuery("question", cached[c], c) for c in case_ids if cached.get(c)]


def save_queries(queries: list[EvalQuery], path: Path) -> None:
    path.write_text(
        json.dumps([asdict(q) for q in queries], ensure_ascii=False, indent=1), encoding="utf-8"
    )


async def evaluate(
    retriever: RetrieverPort,
    queries: list[EvalQuery],
    methods: list[RetrievalMethod],
    depth: int = 40,
) -> list[dict[str, float | str | int]]:
    scores: dict[tuple[str, str], MethodScore] = {}
    for method in methods:
        for query in queries:
            key = (method.value, query.kind)
            score = scores.setdefault(key, MethodScore(method.value, query.kind))
            start = time.perf_counter()
            hits = await retriever.search(query.text, k=depth, method=method)
            score.latency_ms += (time.perf_counter() - start) * 1000
            ranked: list[str] = []
            for hit in hits:  # classement des décisions : premier passage de chacune
                if hit.passage.case_id not in ranked:
                    ranked.append(hit.passage.case_id)
            score.n += 1
            if query.case_id in ranked[:10]:
                rank = ranked.index(query.case_id) + 1
                score.reciprocal_ranks += 1 / rank
                for k in score.hits:
                    if rank <= k:
                        score.hits[k] += 1
    return [s.as_row() for s in scores.values()]
