"""Index lexical (BM25), index dense (embeddings) et recherche hybride (RRF).

- BM25 : bm25s, minuscules, stopwords français, racinisation Snowball française. Le motif
  de tokens garde les numéros composés (« 2312-18 », « 21-23 ») en un seul token, ce qui
  compte pour la jurisprudence (force du lexical sur codes et références).
- Dense : vecteurs normalisés, recherche exacte par produit scalaire (= cosinus). Avec
  quelques dizaines de milliers de passages, la force brute répond en millisecondes ;
  un index ANN n'apporterait que de l'approximation.
- Hybride : Reciprocal Rank Fusion, k=60 (Cormack et al. 2009).
"""

import json
import logging
from collections.abc import Sequence
from pathlib import Path

import bm25s
import numpy as np
import Stemmer

from jurirag.application.ports import EmbedderPort
from jurirag.domain.models import PassageHit, RetrievalMethod
from jurirag.infrastructure.case_store import SqliteCaseStore

logger = logging.getLogger(__name__)

TOKEN_PATTERN = r"(?u)\b\w[\w\-]*\w\b"
_STEMMER = Stemmer.Stemmer("french")

# Qwen3-Embedding est entraîné avec une instruction côté requête (pas côté document).
QUERY_INSTRUCTIONS = {
    "qwen3-embedding": (
        "Instruct: Étant donné une question juridique, retrouver les passages de décisions "
        "de justice qui y répondent\nQuery: "
    ),
}


def query_prefix(embed_model: str) -> str:
    for family, prefix in QUERY_INSTRUCTIONS.items():
        if embed_model.startswith(family):
            return prefix
    return ""


def tokenize(texts: Sequence[str]) -> bm25s.tokenization.Tokenized:
    return bm25s.tokenize(
        list(texts),
        token_pattern=TOKEN_PATTERN,
        stopwords="fr",
        stemmer=_STEMMER.stemWords,
        show_progress=False,
    )


class BM25Index:
    def __init__(self, retriever: bm25s.BM25) -> None:
        self._retriever = retriever

    @classmethod
    def build(cls, texts: Sequence[str]) -> "BM25Index":
        retriever = bm25s.BM25()  # k1=1,5 ; b=0,75 (valeurs usuelles)
        retriever.index(tokenize(texts), show_progress=False)
        return cls(retriever)

    def save(self, directory: Path) -> None:
        self._retriever.save(directory, show_progress=False)

    @classmethod
    def load(cls, directory: Path) -> "BM25Index":
        return cls(bm25s.BM25.load(directory, mmap=True, show_progress=False))

    @property
    def size(self) -> int:
        return int(self._retriever.scores["num_docs"])

    def search(
        self, query: str, k: int, restrict_to: Sequence[int] | None = None
    ) -> list[tuple[int, float]]:
        tokens = tokenize([query])
        if not tokens.ids or not tokens.ids[0]:  # requête vide après stopwords
            return []
        mask = None
        if restrict_to is not None:
            mask = np.zeros(self.size, dtype=np.float32)
            mask[list(restrict_to)] = 1.0
            k = min(k, len(restrict_to))
        rows, scores = self._retriever.retrieve(
            tokens, k=min(k, self.size), show_progress=False, weight_mask=mask
        )
        return [(int(r), float(s)) for r, s in zip(rows[0], scores[0], strict=True) if s > 0]


class DenseIndex:
    def __init__(self, matrix: np.ndarray) -> None:
        self._matrix = matrix

    @staticmethod
    def normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        result: np.ndarray = (vectors / np.clip(norms, 1e-12, None)).astype(np.float32)
        return result

    def save(self, path: Path) -> None:
        np.save(path, self._matrix)

    @classmethod
    def load(cls, path: Path) -> "DenseIndex":
        return cls(np.load(path, mmap_mode="r"))

    @property
    def size(self) -> int:
        return int(self._matrix.shape[0])

    def search(
        self, query_vector: Sequence[float], k: int, restrict_to: Sequence[int] | None = None
    ) -> list[tuple[int, float]]:
        q = self.normalize(np.asarray([query_vector], dtype=np.float32))[0]
        if restrict_to is not None:
            rows = np.asarray(restrict_to, dtype=np.int64)
            sub = np.asarray(self._matrix[rows]) @ q
            order = np.argsort(-sub)[:k]
            return [(int(rows[i]), float(sub[i])) for i in order]
        scores = self._matrix @ q
        k = min(k, scores.shape[0])
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [(int(i), float(scores[i])) for i in top]


def rrf(rankings: Sequence[Sequence[int]], k: int = 60) -> list[tuple[int, float]]:
    """Fusion par rangs : score = Σ 1 / (k + rang). N'utilise que les rangs, pas les scores."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            fused[row] = fused.get(row, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda item: item[1], reverse=True)


class HybridRetriever:
    """Implémente `RetrieverPort` au-dessus des deux index et du stockage des passages."""

    def __init__(
        self,
        store: SqliteCaseStore,
        bm25: BM25Index,
        dense: DenseIndex | None,
        embedder: EmbedderPort | None,
        default_method: RetrievalMethod,
        candidates: int = 50,
        rrf_k: int = 60,
    ) -> None:
        self._store = store
        self._bm25 = bm25
        self._dense = dense
        self._embedder = embedder
        self._candidates = candidates
        self._rrf_k = rrf_k
        self._default = default_method if dense is not None else RetrievalMethod.BM25

    @property
    def available_methods(self) -> list[RetrievalMethod]:
        if self._dense is None:
            return [RetrievalMethod.BM25]
        return [RetrievalMethod.BM25, RetrievalMethod.DENSE, RetrievalMethod.HYBRID]

    @property
    def default_method(self) -> RetrievalMethod:
        return self._default

    async def _dense_search(
        self, query: str, k: int, restrict_to: Sequence[int] | None = None
    ) -> list[tuple[int, float]]:
        assert self._dense is not None and self._embedder is not None
        [vector] = await self._embedder.embed([query_prefix(self._embedder.model) + query])
        return self._dense.search(vector, k, restrict_to)

    async def search(
        self, query: str, k: int, method: RetrievalMethod | None = None
    ) -> list[PassageHit]:
        method = method or self._default
        if method not in self.available_methods:
            method = RetrievalMethod.BM25
        if method == RetrievalMethod.BM25:
            scored = self._bm25.search(query, k)
        elif method == RetrievalMethod.DENSE:
            scored = await self._dense_search(query, k)
        else:
            depth = max(self._candidates, k)
            lexical = [row for row, _ in self._bm25.search(query, depth)]
            dense = [row for row, _ in await self._dense_search(query, depth)]
            scored = rrf([lexical, dense], self._rrf_k)[:k]

        return self._hits(scored)

    async def search_in_case(self, query: str, case_id: str, k: int) -> list[PassageHit]:
        rows = self._store.rows_of_case(case_id)
        if not rows:
            return []
        lexical = [row for row, _ in self._bm25.search(query, len(rows), restrict_to=rows)]
        if self._dense is None:
            return self._hits([(r, 1.0 / (self._rrf_k + i)) for i, r in enumerate(lexical, 1)][:k])
        dense = [row for row, _ in await self._dense_search(query, len(rows), restrict_to=rows)]
        return self._hits(rrf([lexical, dense], self._rrf_k)[:k])

    def _hits(self, scored: Sequence[tuple[int, float]]) -> list[PassageHit]:
        passages = self._store.passages_by_rows([row for row, _ in scored])
        return [
            PassageHit(passage=p, score=round(score, 6), rank=rank)
            for rank, (p, (_, score)) in enumerate(zip(passages, scored, strict=False), start=1)
        ]


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def read_manifest(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data
