"""Stockage SQLite des décisions et des passages (écrit par le job d'indexation, lu par l'API)."""

import json
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

from jurirag.domain.models import Case, CaseMeta, Passage, Zone, ZoneSpan

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    meta    TEXT NOT NULL,
    text    TEXT NOT NULL,
    zones   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS passages (
    row        INTEGER PRIMARY KEY,  -- position de la ligne dans les index BM25 et dense
    passage_id TEXT UNIQUE NOT NULL,
    case_id    TEXT NOT NULL REFERENCES cases(case_id),
    zone       TEXT NOT NULL,
    ordinal    INTEGER NOT NULL,
    start      INTEGER NOT NULL,
    end        INTEGER NOT NULL,
    text       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS passages_case ON passages(case_id);
"""


def _passage(row: sqlite3.Row) -> Passage:
    return Passage(
        passage_id=row["passage_id"],
        case_id=row["case_id"],
        zone=Zone(row["zone"]),
        ordinal=row["ordinal"],
        start=row["start"],
        end=row["end"],
        text=row["text"],
    )


class SqliteCaseStore:
    def __init__(self, path: Path, read_only: bool = True) -> None:
        self._path = path
        if read_only:
            self._conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.executescript(_SCHEMA)
        self._conn.row_factory = sqlite3.Row

    # --- écriture (job d'indexation) ---

    def add(self, case: Case, passages: Iterable[Passage], first_row: int) -> int:
        self._conn.execute(
            "INSERT INTO cases VALUES (?, ?, ?, ?)",
            (
                case.meta.case_id,
                case.meta.model_dump_json(),
                case.text,
                json.dumps([s.model_dump(mode="json") for s in case.zones]),
            ),
        )
        row = first_row
        for p in passages:
            self._conn.execute(
                "INSERT INTO passages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (row, p.passage_id, p.case_id, p.zone.value, p.ordinal, p.start, p.end, p.text),
            )
            row += 1
        return row

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- lecture (CaseRepository) ---

    def get_case(self, case_id: str) -> Case | None:
        row = self._conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if row is None:
            return None
        return Case(
            meta=CaseMeta.model_validate_json(row["meta"]),
            text=row["text"],
            zones=[ZoneSpan.model_validate(z) for z in json.loads(row["zones"])],
        )

    def get_meta(self, case_id: str) -> CaseMeta | None:
        row = self._conn.execute("SELECT meta FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        return None if row is None else CaseMeta.model_validate_json(row["meta"])

    def passages_of(self, case_id: str) -> list[Passage]:
        rows = self._conn.execute(
            "SELECT * FROM passages WHERE case_id = ? ORDER BY start", (case_id,)
        ).fetchall()
        return [_passage(r) for r in rows]

    def get_passages(self, passage_ids: Sequence[str]) -> list[Passage]:
        if not passage_ids:
            return []
        marks = ",".join("?" * len(passage_ids))
        rows = self._conn.execute(
            f"SELECT * FROM passages WHERE passage_id IN ({marks})", list(passage_ids)
        ).fetchall()
        by_id = {r["passage_id"]: _passage(r) for r in rows}
        return [by_id[i] for i in passage_ids if i in by_id]

    def passages_by_rows(self, rows: Sequence[int]) -> list[Passage]:
        if not rows:
            return []
        marks = ",".join("?" * len(rows))
        found = self._conn.execute(
            f"SELECT * FROM passages WHERE row IN ({marks})", [int(r) for r in rows]
        ).fetchall()
        by_row = {r["row"]: _passage(r) for r in found}
        return [by_row[r] for r in rows if r in by_row]

    def rows_of_case(self, case_id: str) -> list[int]:
        found = self._conn.execute(
            "SELECT row FROM passages WHERE case_id = ? ORDER BY row", (case_id,)
        ).fetchall()
        return [int(r["row"]) for r in found]

    def iter_passage_texts(self) -> Iterable[tuple[int, str]]:
        yield from self._conn.execute("SELECT row, text FROM passages ORDER BY row")

    def all_metas(self) -> list[CaseMeta]:
        return [
            CaseMeta.model_validate_json(r["meta"])
            for r in self._conn.execute("SELECT meta FROM cases ORDER BY case_id")
        ]

    def count_cases(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0])

    def count_passages(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM passages").fetchone()[0])
