"""Job d'indexation hors ligne : corpus → passages → BM25 + embeddings → manifeste.

L'indexation est faite une fois, hors ligne ; l'API ne fait que lire.
Reconstruction reproductible : révision du dataset figée, graine fixe, paramètres consignés.
"""

import logging
import shutil
import time
from dataclasses import asdict
from datetime import UTC, datetime

import httpx
import numpy as np

from jurirag.application.chunking import chunk_case
from jurirag.config import Settings
from jurirag.domain.models import Provenance
from jurirag.infrastructure.case_store import SqliteCaseStore
from jurirag.infrastructure.corpus import (
    SelectionCriteria,
    download_split,
    iter_cases,
    select_rows,
)
from jurirag.infrastructure.indexes import BM25Index, DenseIndex, write_manifest
from jurirag.infrastructure.ollama import OllamaEmbedder

logger = logging.getLogger(__name__)

EMBED_BATCH = 32


async def _embed_all(store: SqliteCaseStore, settings: Settings, embed_model: str) -> np.ndarray:
    rows = list(store.iter_passage_texts())
    vectors: list[list[float]] = []
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=settings.request_timeout_s) as http:
        embedder = OllamaEmbedder(http, settings.ollama_base_url, embed_model)
        for i in range(0, len(rows), EMBED_BATCH):
            batch = [text for _, text in rows[i : i + EMBED_BATCH]]
            vectors.extend(await embedder.embed(batch))
            if (i // EMBED_BATCH) % 50 == 0:
                done = i + len(batch)
                rate = done / max(time.perf_counter() - start, 1e-6)
                logger.info("embeddings %d/%d (%.0f passages/s)", done, len(rows), rate)
    return DenseIndex.normalize(np.asarray(vectors, dtype=np.float32))


async def build_index(
    settings: Settings,
    criteria: SelectionCriteria,
    embed_model: str | None,
    with_dense: bool = True,
) -> dict[str, object]:
    started = time.perf_counter()
    out = settings.index_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    parquet = download_split(
        settings.dataset_repo, settings.dataset_revision, settings.dataset_split, settings.raw_dir
    )
    logger.info("sélection des décisions dans %s", parquet)
    rows, report = select_rows(parquet, criteria)
    provenance = Provenance(
        dataset=settings.dataset_repo,
        revision=settings.dataset_revision,
        split=settings.dataset_split,
    )

    store = SqliteCaseStore(out / "cases.db", read_only=False)
    next_row = 0
    n_cases = 0
    for case in iter_cases(parquet, rows, provenance, report):
        passages = chunk_case(case, settings.chunk_tokens, settings.chunk_overlap)
        next_row = store.add(case, passages, next_row)
        n_cases += 1
        if n_cases % 1000 == 0:
            store.commit()
            logger.info("%d décisions, %d passages", n_cases, next_row)
    store.commit()

    texts = [text for _, text in store.iter_passage_texts()]
    logger.info("index BM25 sur %d passages", len(texts))
    BM25Index.build(texts).save(out / "bm25")

    dense_seconds = None
    if with_dense and embed_model:
        t0 = time.perf_counter()
        matrix = await _embed_all(store, settings, embed_model)
        DenseIndex(matrix).save(out / "dense.npy")
        dense_seconds = round(time.perf_counter() - t0, 1)
    store.close()

    manifest: dict[str, object] = {
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset": settings.dataset_repo,
        "revision": settings.dataset_revision,
        "split": settings.dataset_split,
        "license": "Etalab 2.0",
        "criteria": {**asdict(criteria), "years": list(criteria.years)},
        "rows_in_split": report.rows_total,
        "candidates": report.candidates,
        "selected_rows": report.selected,
        "published_selected": report.published_selected,
        "rejected": dict(report.rejected),
        "cases": n_cases,
        "passages": next_row,
        "chunk_tokens": settings.chunk_tokens,
        "chunk_overlap": settings.chunk_overlap,
        "embed_model": embed_model if with_dense else None,
        "dense_seconds": dense_seconds,
        "total_seconds": round(time.perf_counter() - started, 1),
    }
    write_manifest(out / "manifest.json", manifest)
    return manifest
