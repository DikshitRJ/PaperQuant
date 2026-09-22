from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AlgorithmStore:
    def __init__(self, base_dir: str | Path, db_path: str | Path):
        self.algorithms_dir = Path(base_dir) / "algorithms"
        self.algorithms_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""CREATE TABLE IF NOT EXISTS algorithms (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, filename TEXT NOT NULL,
                dependencies TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS algorithm_runs (
                run_id TEXT PRIMARY KEY, algorithm_id TEXT NOT NULL, date TEXT NOT NULL,
                pnl TEXT DEFAULT '$0.00', status TEXT DEFAULT 'Running',
                duration_seconds INTEGER DEFAULT 0, started_at TEXT NOT NULL DEFAULT '');""")
            cols = {row[1] for row in conn.execute("PRAGMA table_info(algorithm_runs)")}
            if "started_at" not in cols:
                conn.execute("ALTER TABLE algorithm_runs ADD COLUMN started_at TEXT NOT NULL DEFAULT ''")

    def list_algorithms(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM algorithms ORDER BY created_at DESC").fetchall()
            result = []
            for row in rows:
                runs = conn.execute("SELECT * FROM algorithm_runs WHERE algorithm_id=? ORDER BY date DESC",
                                    (row["id"],)).fetchall()
                result.append({**dict(row), "dependencies": json.loads(row["dependencies"]),
                               "history": [dict(run) for run in runs]})
            return result

    def get(self, algorithm_id: str) -> dict | None:
        return next((a for a in self.list_algorithms() if a["id"] == algorithm_id), None)

    def register(self, name: str, filename: str, dependencies: list[str], content: bytes) -> dict:
        if not filename.endswith(".py") or Path(filename).name != filename or not content:
            raise ValueError("file_invalid")
        algorithm_id = re.sub(r"[^a-z0-9_]+", "_", Path(filename).stem.lower()).strip("_")
        if not algorithm_id:
            raise ValueError("file_invalid")
        now = datetime.now(timezone.utc).isoformat()
        target = self.algorithms_dir / filename
        target.write_bytes(content)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO algorithms VALUES (?, ?, ?, ?, ?)",
                         (algorithm_id, name, filename, json.dumps(dependencies), now))
        return {"id": algorithm_id, "name": name, "filename": filename, "dependencies": dependencies, "created_at": now,
                "history": []}

    def delete(self, algorithm_id: str) -> bool:
        algo = self.get(algorithm_id)
        if not algo:
            return False
        (self.algorithms_dir / algo["filename"]).unlink(missing_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM algorithm_runs WHERE algorithm_id=?", (algorithm_id,))
            conn.execute("DELETE FROM algorithms WHERE id=?", (algorithm_id,))
        return True

    def get_script_path(self, algorithm_id: str) -> Path | None:
        algo = self.get(algorithm_id)
        return self.algorithms_dir / algo["filename"] if algo else None

    def start_run(self, algorithm_id: str) -> dict:
        now = datetime.now(timezone.utc)
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO algorithm_runs(run_id, algorithm_id, date, pnl, status, duration_seconds, started_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, algorithm_id, now.date().isoformat(), "$0.00", "Running", 0, now.isoformat()),
            )
        return {"run_id": run_id, "date": now.date().isoformat(), "status": "Running"}

    def find_active_run(self, algorithm_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM algorithm_runs WHERE algorithm_id=? AND status='Running' "
                "ORDER BY started_at DESC, date DESC LIMIT 1",
                (algorithm_id,),
            ).fetchone()
            return dict(row) if row else None

    def finish_run(self, run_id: str, status: str = "Stopped", pnl: str = "$0.00") -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT started_at FROM algorithm_runs WHERE run_id=?", (run_id,)).fetchone()
            if not row:
                return False
            started_at = row["started_at"]
            duration = 0
            if started_at:
                try:
                    start_dt = datetime.fromisoformat(started_at)
                    duration = max(0, int((datetime.now(timezone.utc) - start_dt).total_seconds()))
                except ValueError:
                    duration = 0
            conn.execute(
                "UPDATE algorithm_runs SET status=?, pnl=?, duration_seconds=? WHERE run_id=?",
                (status, pnl, duration, run_id),
            )
        return True
