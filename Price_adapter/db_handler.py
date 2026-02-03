import sqlite3
from datetime import datetime, timezone
from diskcache import Cache
import json


def _normalize_timestamp(ts):
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    return ts.replace(second=0, microsecond=0)


def imt_sqlite(
    data,
    db_path="./Temporary/paperquant.db",
    table_name="candles"
):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(symbol, timestamp)
            )
        """)

        if not data:
            return 0

        # ---- DEDUPLICATE IN MEMORY ----
        seen = set()
        rows = []

        for d in data:
            ts = _normalize_timestamp(d["timestamp"]).isoformat()
            key = (d["symbol"], ts)

            if key in seen:
                continue

            seen.add(key)
            rows.append((
                d["symbol"],
                d["open"],
                d["high"],
                d["low"],
                d["close"],
                d["volume"],
                ts
            ))

        if not rows:
            return 0

        before = conn.total_changes

        cursor.executemany(
            f"""
            INSERT OR IGNORE INTO {table_name}
            (symbol, open, high, low, close, volume, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows
        )

        conn.commit()
        return conn.total_changes - before

    finally:
        if conn:
            conn.close()


# ---------------- DISKCACHE ----------------

cache = Cache("./Temporary/cache_candles")


def update_diskcache_candles(ticker: str, candle_data: dict):
    try:
        cache_key = f"candles:{ticker}"
        candles = cache.get(cache_key, [])

        ts = _normalize_timestamp(candle_data["timestamp"]).isoformat()
        candle_data = dict(candle_data)
        candle_data["timestamp"] = ts

        normalized = []

        for c in candles:
            # Old format (JSON string)
            if isinstance(c, str):
                try:
                    c = json.loads(c)
                except Exception:
                    continue

            # New format (dict)
            if isinstance(c, dict) and c.get("timestamp") != ts:
                normalized.append(c)

        normalized.append(candle_data)
        normalized = normalized[-5:]

        cache.set(cache_key, normalized)

    except Exception as e:
        print(f"An error occurred while updating DiskCache cache: {e}")
        raise
