"""Composition root : le seul endroit où les adapters concrets sont câblés aux ports.

L'API, la CLI d'évaluation et les tests d'intégration passent par ici ; les tests unitaires
construisent directement les objets de l'application avec des doublures.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from jurirag.config import Settings
from jurirag.domain.errors import IndexNotReadyError
from jurirag.infrastructure.case_store import SqliteCaseStore
from jurirag.infrastructure.indexes import BM25Index, DenseIndex, HybridRetriever, read_manifest
from jurirag.infrastructure.ollama import OllamaClient, OllamaEmbedder


@dataclass
class IndexBundle:
    store: SqliteCaseStore
    retriever: HybridRetriever
    manifest: dict[str, Any]
    embedder: OllamaEmbedder | None


def load_index(
    settings: Settings, http: httpx.AsyncClient, index_dir: Path | None = None
) -> IndexBundle:
    directory = index_dir or settings.index_dir
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise IndexNotReadyError(
            f"Index absent dans {directory} — lancer `make index` (jurirag-build)."
        )
    manifest = read_manifest(manifest_path)
    store = SqliteCaseStore(directory / "cases.db", read_only=True)
    bm25 = BM25Index.load(directory / "bm25")
    dense = embedder = None
    embed_model = manifest.get("embed_model")
    if (directory / "dense.npy").exists() and isinstance(embed_model, str):
        dense = DenseIndex.load(directory / "dense.npy")
        # La requête doit être encodée par le même modèle que les passages.
        embedder = OllamaEmbedder(http, settings.ollama_base_url, embed_model)
    retriever = HybridRetriever(
        store,
        bm25,
        dense,
        embedder,
        default_method=settings.retrieval_method,
        candidates=settings.retrieval_candidates,
        rrf_k=settings.rrf_k,
    )
    return IndexBundle(store=store, retriever=retriever, manifest=manifest, embedder=embedder)


@asynccontextmanager
async def http_client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=settings.request_timeout_s) as http:
        yield http


def make_llm(settings: Settings, http: httpx.AsyncClient) -> OllamaClient:
    return OllamaClient(http, settings.ollama_base_url, keep_alive=settings.ollama_keep_alive)
