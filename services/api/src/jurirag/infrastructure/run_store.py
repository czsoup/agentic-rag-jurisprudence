"""Journal des runs et des événements de trace, en SQLite.

Ne stocke que ce qui sert à analyser une exécution : question, mode, modèle, événements,
métriques, réponse. Aucune donnée d'identification de l'utilisateur ; la session est un
identifiant aléatoire généré par l'interface.
"""

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jurirag.domain.trace import RunMetrics, TraceEvent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    question    TEXT NOT NULL,
    mode        TEXT NOT NULL,
    model       TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    metrics     TEXT,
    answer      TEXT
);
CREATE TABLE IF NOT EXISTS events (
    run_id     TEXT NOT NULL,
    step       INTEGER NOT NULL,
    type       TEXT NOT NULL,
    agent      TEXT NOT NULL,
    summary    TEXT NOT NULL,
    data       TEXT NOT NULL,
    latency_ms REAL,
    at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_run ON events(run_id, step);
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    payload     TEXT NOT NULL,
    created_at  REAL NOT NULL,
    decided_at  REAL,
    decision    TEXT
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class SqliteRunStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._lock = threading.Lock()

    def start_run(self, run_id: str, session_id: str, question: str, mode: str, model: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs (run_id, session_id, question, mode, model, started_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, session_id, question, mode, model, _now()),
            )
            self._conn.commit()

    def save_event(self, event: TraceEvent) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.run_id,
                    event.step,
                    event.type.value,
                    event.agent,
                    event.summary,
                    json.dumps(event.data, ensure_ascii=False),
                    event.latency_ms,
                    event.at,
                ),
            )
            self._conn.commit()

    def finish_run(self, run_id: str, metrics: RunMetrics, answer: str | None) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET finished_at = ?, metrics = ?, answer = ? WHERE run_id = ?",
                (_now(), metrics.model_dump_json(), answer, run_id),
            )
            self._conn.commit()

    def _run(self, row: sqlite3.Row) -> dict[str, Any]:
        run = dict(row)
        run["metrics"] = json.loads(run["metrics"]) if run["metrics"] else None
        return run

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._run(r) for r in rows]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        run = self._run(row)
        events = self._conn.execute(
            "SELECT * FROM events WHERE run_id = ? ORDER BY step", (run_id,)
        ).fetchall()
        run["events"] = [{**dict(e), "data": json.loads(e["data"])} for e in events]
        return run

    # --- validations humaines hors graphe (export du dossier) ---

    def create_approval(
        self, approval_id: str, kind: str, payload: dict[str, Any], created_at: float
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO approvals (approval_id, kind, payload, created_at) VALUES (?, ?, ?, ?)",
                (approval_id, kind, json.dumps(payload, ensure_ascii=False), created_at),
            )
            self._conn.commit()

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
        ).fetchone()
        if row is None:
            return None
        approval = dict(row)
        approval["payload"] = json.loads(approval["payload"])
        return approval

    def decide_approval(self, approval_id: str, decision: str, decided_at: float) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE approvals SET decision = ?, decided_at = ? WHERE approval_id = ? AND decision IS NULL",
                (decision, decided_at, approval_id),
            )
            self._conn.commit()
