import sqlite3
from datetime import datetime
from diskcache import Cache
import json

def imt_sqlite(
    data,
    db_path="./Temporary/paperquant.db",
    table_name="candles"
):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fixed candle schema
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                UNIQUE(symbol, timestamp)
            )
        """)

        if not data:
            print("No data to insert.")
            return None

        rows = [
            (
                d["symbol"],
                d["open"],
                d["high"],
                d["low"],
                d["close"],
                d["volume"],
                d["timestamp"].isoformat()
                if isinstance(d["timestamp"], datetime)
                else d["timestamp"]
            )
            for d in data
        ]

        cursor.executemany(
            f"""
            INSERT OR IGNORE INTO {table_name}
            (symbol, open, high, low, close, volume, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows
        )

        conn.commit()
        return cursor.rowcount

    except Exception as e:
        print(f"An error occurred while inserting candle data: {e}")
        raise

    finally:
        if conn:
            conn.close()



cache = Cache("./Temporary/cache_candles")  # creates directory automatically

def _json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def update_diskcache_candles(ticker: str, candle_data: dict):
    try:
        cache_key = f"candles:{ticker}"

        # Load existing list or initialize
        candles = cache.get(cache_key, [])

        candles.append(
            json.dumps(candle_data, default=_json_serializer)
        )

        # Keep only last 5 candles
        candles = candles[-5:]

        # Persist back to disk
        cache.set(cache_key, candles)

    except Exception as e:
        print(f"An error occurred while updating DiskCache cache: {e}")
        raise