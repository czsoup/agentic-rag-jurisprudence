"""Commandes en ligne : construction de l'index et évaluation du retrieval."""

import asyncio
import json
from typing import Annotated

import typer

from jurirag.config import get_settings
from jurirag.logging_config import configure_logging


def _build(
    n: Annotated[int, typer.Option(help="Nombre de décisions à indexer")] = 8000,
    year_from: Annotated[int, typer.Option(help="Première année incluse")] = 2022,
    year_to: Annotated[int, typer.Option(help="Dernière année incluse")] = 2024,
    published_share: Annotated[float, typer.Option(help="Part d'arrêts publiés au Bulletin")] = 0.5,
    embed_model: Annotated[str | None, typer.Option(help="Modèle d'embedding Ollama")] = None,
    no_dense: Annotated[bool, typer.Option("--no-dense", help="BM25 seulement")] = False,
    index_name: Annotated[str | None, typer.Option(help="Nom du dossier d'index")] = None,
    seed: Annotated[int, typer.Option(help="Graine de l'échantillonnage")] = 42,
) -> None:
    """Télécharge le corpus, sélectionne les décisions et construit les index."""
    from jurirag.infrastructure.corpus import SelectionCriteria
    from jurirag.infrastructure.index_builder import build_index

    settings = get_settings()
    if index_name:
        settings = settings.model_copy(update={"index_name": index_name})
    configure_logging(settings.log_level)
    criteria = SelectionCriteria(
        years=(year_from, year_to), n=n, published_share=published_share, seed=seed
    )
    manifest = asyncio.run(
        build_index(
            settings,
            criteria,
            embed_model or settings.ollama_embed_model,
            with_dense=not no_dense,
        )
    )
    typer.echo(json.dumps(manifest, ensure_ascii=False, indent=2))


def build() -> None:
    typer.run(_build)


def _evaluate(
    n: Annotated[int, typer.Option(help="Arrêts publiés tirés comme pseudo-requêtes")] = 150,
    index_name: Annotated[str | None, typer.Option(help="Nom du dossier d'index")] = None,
    out: Annotated[
        str, typer.Option(help="Préfixe des fichiers de résultats")
    ] = "docs/results/retrieval",
    seed: Annotated[int, typer.Option(help="Graine du tirage")] = 42,
    paraphrase: Annotated[
        bool, typer.Option(help="Ajouter des questions reformulées par le LLM")
    ] = True,
) -> None:
    """Compare BM25, dense et hybride (Hit@k, MRR) sur des pseudo-requêtes issues du corpus."""
    import csv
    from pathlib import Path

    from jurirag.application.retrieval_eval import (
        add_paraphrases,
        build_queries,
        evaluate,
        save_queries,
    )
    from jurirag.bootstrap import http_client, load_index, make_llm

    settings = get_settings()
    if index_name:
        settings = settings.model_copy(update={"index_name": index_name})
    configure_logging(settings.log_level)

    async def main() -> list[dict[str, float | str | int]]:
        async with http_client(settings) as http:
            bundle = load_index(settings, http)
            metas = bundle.store.all_metas()
            queries = build_queries(metas, n, seed)
            if paraphrase:
                queries = await add_paraphrases(
                    queries,
                    {m.case_id: m for m in metas},
                    make_llm(settings, http),
                    settings.generation_params(temperature=0.0),
                    Path(f"{out}_questions_{settings.index_name}.json"),
                )
            save_queries(queries, Path(f"{out}_queries_{settings.index_name}.json"))
            rows = await evaluate(bundle.retriever, queries, bundle.retriever.available_methods)
            for row in rows:
                row["index"] = settings.index_name
                row["embed_model"] = str(bundle.manifest.get("embed_model"))
                row["cases"] = int(str(bundle.manifest.get("cases", 0)))
            return rows

    rows = asyncio.run(main())
    path = Path(f"{out}_{settings.index_name}.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    header = "| " + " | ".join(rows[0]) + " |"
    lines = [header, "|" + "---|" * len(rows[0])] + [
        "| " + " | ".join(str(v) for v in r.values()) + " |" for r in rows
    ]
    path.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    typer.echo("\n".join(lines))


def evaluate() -> None:
    typer.run(_evaluate)
