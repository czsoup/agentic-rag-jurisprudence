"""Chargement du dataset `antoinejeannot/jurisprudence` et sélection du sous-corpus.

Le parquet de la Cour de cassation (1,72 Go, un seul row group) est lu en deux passes :
1. colonnes légères uniquement (date, chambre, zones, publication…) → sélection des lignes ;
2. lecture en flux (`iter_batches`) du texte des seules lignes retenues.
La mémoire reste bornée et la sélection est reproductible (graine fixe, filtres consignés).
"""

import logging
import random
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from jurirag.domain.models import Case, CaseMeta, Provenance, Zone, ZoneSpan

logger = logging.getLogger(__name__)

LIGHT_COLUMNS = ["decision_date", "chamber", "zones", "publication", "solution"]
FULL_COLUMNS = [
    "id",
    "jurisdiction",
    "chamber",
    "formation",
    "type",
    "decision_date",
    "number",
    "ecli",
    "solution",
    "publication",
    "themes",
    "summary",
    "visa",
    "contested",
    "zones",
    "text",
]

# Ordonnances du premier président, déchéances, désistements : décisions de procédure,
# sans motivation au fond — peu utiles pour un assistant de recherche jurisprudentielle.
DEFAULT_CHAMBERS = (
    "Chambre sociale",
    "Première chambre civile",
    "Deuxième chambre civile",
    "Troisième chambre civile",
    "Chambre commerciale financière et économique",
    "Chambre criminelle",
)
EXCLUDED_SOLUTIONS = ("Déchéance", "Désistement", "Non-lieu à statuer")

_HTML_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


def download_split(repo: str, revision: str, split: str, raw_dir: Path) -> Path:
    """Télécharge (une fois) le parquet d'un split, à une révision figée du dataset."""
    path = hf_hub_download(
        repo, f"{split}.parquet", repo_type="dataset", revision=revision, local_dir=raw_dir
    )
    return Path(path)


def normalize_text(text: str) -> str:
    """Normalisation minimale et sans perte juridique : espaces et lignes vides.

    Ne touche ni à la casse, ni à la ponctuation, ni aux références (« article L. 1234-5 »).
    Les offsets du champ `zones` étant calculés sur le texte d'origine, la normalisation
    est appliquée zone par zone au moment de la construction de la décision (voir `to_case`).
    """
    text = _SPACES.sub(" ", text)
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


@dataclass
class SelectionReport:
    """Ce qui a été lu, retenu et rejeté, pour le manifeste de provenance."""

    rows_total: int = 0
    candidates: int = 0
    selected: int = 0
    rejected: Counter[str] = field(default_factory=Counter)
    published_selected: int = 0


@dataclass(frozen=True)
class SelectionCriteria:
    years: tuple[int, int] = (2022, 2024)
    chambers: tuple[str, ...] = DEFAULT_CHAMBERS
    n: int = 8000
    # Les arrêts publiés au Bulletin (porteurs d'un sommaire) sont pris en priorité :
    # jurisprudence significative et sommaires utilisables pour évaluer le retrieval.
    published_share: float = 0.5
    seed: int = 42


def select_rows(parquet: Path, criteria: SelectionCriteria) -> tuple[list[int], SelectionReport]:
    table = pq.read_table(parquet, columns=LIGHT_COLUMNS)
    report = SelectionReport(rows_total=table.num_rows)
    dates = table["decision_date"].to_pylist()
    chambers = table["chamber"].to_pylist()
    zones = table["zones"].to_pylist()
    publications = table["publication"].to_pylist()
    solutions = table["solution"].to_pylist()

    lo, hi = str(criteria.years[0]), str(criteria.years[1])
    published: list[int] = []
    others: list[int] = []
    for i, date in enumerate(dates):
        year = (date or "")[:4]
        if not (lo <= year <= hi):
            continue
        if chambers[i] not in criteria.chambers:
            report.rejected["chambre hors périmètre"] += 1
            continue
        if solutions[i] in EXCLUDED_SOLUTIONS:
            report.rejected["décision de procédure"] += 1
            continue
        if not zones[i] or not any(zones[i].get(z) for z in ("motivations", "dispositif")):
            report.rejected["zonage absent ou incomplet"] += 1
            continue
        report.candidates += 1
        if "Publié au Bulletin" in (publications[i] or []):
            published.append(i)
        else:
            others.append(i)

    rng = random.Random(criteria.seed)
    n_published = min(len(published), int(criteria.n * criteria.published_share))
    chosen = rng.sample(published, n_published)
    chosen += rng.sample(others, min(len(others), criteria.n - n_published))
    report.selected = len(chosen)
    report.published_selected = n_published
    return sorted(chosen), report


def _spans(raw_zones: dict[str, Any] | None, text_length: int) -> list[ZoneSpan]:
    spans: list[ZoneSpan] = []
    for name, items in (raw_zones or {}).items():
        try:
            zone = Zone(name)
        except ValueError:
            continue
        for item in items or []:
            start, end = item.get("start"), item.get("end")
            if not (isinstance(start, int) and isinstance(end, int)):
                continue
            # Les offsets de fin dépassent parfois d'un caractère la longueur du texte
            # (observé sur le dataset) : on borne plutôt que de perdre la zone.
            end = min(end, text_length)
            if 0 <= start < end:
                spans.append(ZoneSpan(zone=zone, start=start, end=end))
    return sorted(spans, key=lambda s: s.start)


def to_case(row: dict[str, Any], provenance: Provenance) -> Case | None:
    """Construit une décision ; renvoie None si elle est inexploitable."""
    raw_text = row.get("text") or ""
    if not row.get("id") or len(raw_text.strip()) < 200:
        return None
    spans = _spans(row.get("zones"), len(raw_text))

    # Le texte est reconstruit zone par zone, normalisé, et les offsets recalculés :
    # on garde la structure de l'arrêt sans dépendre des espaces du texte source.
    parts: list[str] = []
    new_spans: list[ZoneSpan] = []
    cursor = 0
    covered = 0
    for span in spans:
        if span.start < covered:  # zones qui se chevauchent : on garde la première
            continue
        chunk = normalize_text(raw_text[span.start : span.end])
        covered = span.end
        if not chunk:
            continue
        if parts:
            cursor += 2
        new_spans.append(ZoneSpan(zone=span.zone, start=cursor, end=cursor + len(chunk)))
        parts.append(chunk)
        cursor += len(chunk)
    text = "\n\n".join(parts) if parts else normalize_text(raw_text)

    contested = row.get("contested") or {}
    # Les titres de visa contiennent des liens HTML vers Légifrance : on garde le texte.
    visa = [
        _SPACES.sub(" ", _HTML_TAG.sub("", v["title"])).strip()
        for v in row.get("visa") or []
        if isinstance(v, dict) and v.get("title")
    ]
    meta = CaseMeta(
        case_id=row["id"],
        jurisdiction=row.get("jurisdiction") or "Cour de cassation",
        chamber=row.get("chamber"),
        formation=row.get("formation"),
        decision_type=row.get("type"),
        decision_date=row.get("decision_date"),
        number=row.get("number"),
        ecli=row.get("ecli"),
        solution=row.get("solution"),
        publication=list(row.get("publication") or []),
        themes=list(row.get("themes") or []),
        summary=(row.get("summary") or "").strip() or None,
        visa=visa,
        contested=contested.get("title") if isinstance(contested, dict) else None,
        provenance=provenance.model_copy(
            update={"url": f"https://www.courdecassation.fr/decision/{row['id']}"}
        ),
    )
    return Case(meta=meta, text=text, zones=new_spans)


def iter_cases(
    parquet: Path, rows: list[int], provenance: Provenance, report: SelectionReport
) -> Iterator[Case]:
    wanted = set(rows)
    seen: set[str] = set()
    offset = 0
    for batch in pq.ParquetFile(parquet).iter_batches(batch_size=4096, columns=FULL_COLUMNS):
        size = batch.num_rows
        local = [i - offset for i in range(offset, offset + size) if i in wanted]
        offset += size
        if not local:
            continue
        for row in batch.take(local).to_pylist():
            case = to_case(row, provenance)
            if case is None:
                report.rejected["texte vide ou trop court"] += 1
                continue
            if case.meta.case_id in seen:
                report.rejected["doublon d'identifiant"] += 1
                continue
            seen.add(case.meta.case_id)
            yield case
