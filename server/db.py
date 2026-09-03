"""SQLite persistence (stdlib sqlite3, one connection, one lock).

Tables: runs (an attempt at an incident), events (everything the user did,
timestamped; the source of every measured number), execs (sandbox executions
for the runtime tab), settings (key/value)."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "var" / "buglab.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  started_at REAL NOT NULL,
  resolved_at REAL,
  hints_revealed INTEGER NOT NULL DEFAULT 0,
  solution_revealed INTEGER NOT NULL DEFAULT 0,
  hypothesis TEXT NOT NULL DEFAULT '',
  reproduced INTEGER NOT NULL DEFAULT 0,
  repro_test_path TEXT,
  score_json TEXT,
  postmortem_json TEXT
);
CREATE INDEX IF NOT EXISTS runs_incident ON runs(incident_id, status);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  ts REAL NOT NULL,
  type TEXT NOT NULL,
  payload TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS events_run ON events(run_id, id);
CREATE TABLE IF NOT EXISTS execs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  ts REAL NOT NULL,
  kind TEXT NOT NULL,
  stdout TEXT NOT NULL,
  stderr TEXT NOT NULL,
  exit_code INTEGER NOT NULL,
  duration_ms INTEGER NOT NULL,
  timed_out INTEGER NOT NULL,
  max_rss_kb INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS execs_run ON execs(run_id, id);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)
        self._lock = threading.RLock()

    def close(self) -> None:
        self._conn.close()

    def _rows(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def _row(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def _exec(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            self._conn.execute(sql, params)

    # --- runs ---------------------------------------------------------------

    def create_run(self, incident_id: str) -> sqlite3.Row:
        run_id = uuid.uuid4().hex[:12]
        self._exec("INSERT INTO runs (id, incident_id, started_at) VALUES (?, ?, ?)", (run_id, incident_id, time.time()))
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> sqlite3.Row | None:
        return self._row("SELECT * FROM runs WHERE id = ?", (run_id,))

    def active_run(self, incident_id: str) -> sqlite3.Row | None:
        return self._row("SELECT * FROM runs WHERE incident_id = ? AND status = 'active' ORDER BY started_at DESC LIMIT 1", (incident_id,))

    def update_run(self, run_id: str, **fields) -> sqlite3.Row:
        cols = ", ".join(f"{k} = ?" for k in fields)
        self._exec(f"UPDATE runs SET {cols} WHERE id = ?", (*fields.values(), run_id))
        return self.get_run(run_id)

    def runs_for(self, incident_id: str) -> list[sqlite3.Row]:
        return self._rows("SELECT * FROM runs WHERE incident_id = ? ORDER BY started_at", (incident_id,))

    def resolved_runs(self) -> list[sqlite3.Row]:
        return self._rows("SELECT * FROM runs WHERE status = 'resolved' ORDER BY resolved_at DESC")

    def attempt_counts(self) -> dict[str, int]:
        return {r["incident_id"]: r["n"] for r in self._rows("SELECT incident_id, COUNT(*) AS n FROM runs GROUP BY incident_id")}

    def best_scores(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self._rows("SELECT incident_id, score_json FROM runs WHERE status = 'resolved' AND score_json IS NOT NULL"):
            total = json.loads(r["score_json"])["total"]
            out[r["incident_id"]] = max(out.get(r["incident_id"], 0), total)
        return out

    def active_runs(self) -> dict[str, str]:
        return {r["incident_id"]: r["id"] for r in self._rows("SELECT incident_id, id FROM runs WHERE status = 'active'")}

    # --- events / execs -----------------------------------------------------

    def add_event(self, run_id: str, type_: str, payload: dict | None = None) -> None:
        self._exec("INSERT INTO events (run_id, ts, type, payload) VALUES (?, ?, ?, ?)", (run_id, time.time(), type_, json.dumps(payload or {})))

    def events(self, run_id: str) -> list[dict]:
        return [{"ts": r["ts"], "type": r["type"], "payload": json.loads(r["payload"])} for r in self._rows("SELECT * FROM events WHERE run_id = ? ORDER BY id", (run_id,))]

    def count_events(self, run_id: str, type_: str) -> int:
        return self._row("SELECT COUNT(*) AS n FROM events WHERE run_id = ? AND type = ?", (run_id, type_))["n"]

    def add_exec(self, run_id: str, kind: str, r) -> None:
        self._exec(
            "INSERT INTO execs (run_id, ts, kind, stdout, stderr, exit_code, duration_ms, timed_out, max_rss_kb) VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, time.time(), kind, r.stdout[-200_000:], r.stderr[-200_000:], r.exit_code, r.duration_ms, int(r.timed_out), r.max_rss_kb),
        )

    def execs(self, run_id: str, limit: int = 30) -> list[sqlite3.Row]:
        return self._rows("SELECT * FROM execs WHERE run_id = ? ORDER BY id DESC LIMIT ?", (run_id, limit))

    # --- settings -----------------------------------------------------------

    def settings(self) -> dict[str, str]:
        return {r["key"]: r["value"] for r in self._rows("SELECT key, value FROM settings")}

    def set_settings(self, values: dict[str, str]) -> None:
        with self._lock:
            for k, v in values.items():
                self._conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (k, str(v)))
