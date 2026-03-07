import os
import sys
import zmq
import time
import logging
from diskcache import Cache
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd

# -------------------------------------------------
# Configuration
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDICATORS_DIR = os.path.join(BASE_DIR, "Indicators")
sys.path.insert(0, INDICATORS_DIR)

ZMQ_ENDPOINT = os.getenv("SIM_TRADE_ENDPOINT", "tcp://127.0.0.1:5555")
CACHE_PATH = os.getenv("SIM_CACHE_PATH", "./Temporary/cache_candles")

STRATEGY_ID = os.getenv("SIM_STRATEGY_ID")
SYMBOL = os.getenv("SIM_SYMBOL")

if not STRATEGY_ID:
    raise RuntimeError("SIM_STRATEGY_ID must be set for each strategy process")

if not SYMBOL:
    raise RuntimeError("SIM_SYMBOL must be set for each strategy process")

# -------------------------------------------------
# Logging
# -------------------------------------------------

logger = logging.getLogger(f"handler.{STRATEGY_ID}.{SYMBOL}")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# -------------------------------------------------
# Indicators exposure
# -------------------------------------------------

from Indicators.Main import indicators as indicators

INTERVAL_TO_DELTA = {
    "1m": timedelta(minutes=1),
    "2m": timedelta(minutes=2),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "60m": timedelta(minutes=60),
    "90m": timedelta(minutes=90),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "5d": timedelta(days=5),
    "1wk": timedelta(weeks=1),
    "1mo": timedelta(days=30),
    "3mo": timedelta(days=90),
}
# -------------------------------------------------
# ZMQ DEALER setup (Async)
# -------------------------------------------------

import zmq.asyncio

_context = zmq.asyncio.Context.instance()
_socket = _context.socket(zmq.DEALER)

# Explicit identity for ROUTER
_socket.setsockopt(zmq.IDENTITY, STRATEGY_ID.encode())

# High/Infinite timeout behavior since limit orders block indefinitely
_socket.setsockopt(zmq.RCVTIMEO, -1)
_socket.setsockopt(zmq.SNDTIMEO, 2000)

_socket.connect(ZMQ_ENDPOINT)

# -------------------------------------------------
# Cache (read-only from Handler POV)
# -------------------------------------------------

_cache = Cache(CACHE_PATH)
def _to_number(val, is_int=False):
    if pd.isna(val):
        return None
    try:
        return int(val) if is_int else float(val)
    except Exception:
        return None


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _ok(data):
    return {
        "status": "ok",
        "data": data
    }

def _error(code, message=None):
    return {
        "status": "error",
        "code": code,
        "message": message
    }

def _now_s():
    return time.time()

def _normalize_timestamp(ts):
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    return ts.replace(second=0, microsecond=0)

# -------------------------------------------------
# Market Data API
# -------------------------------------------------

class prices:
    @staticmethod
    def last_candle(symbol: str = SYMBOL):
        if not isinstance(symbol, str) or not symbol:
            return _error("INVALID_SYMBOL")

        candle = _cache.get(f"candles:{symbol}")

        if candle is None:
            logger.warning(f"No candle for {symbol}")
            return _error("NO_DATA")

        ts = candle.get("timestamp")
        # Stale data check removed as requested
        return _ok(candle)

    @staticmethod
    def candle_list(symbol, no_of_candles, interval, field="all"):
        try:
            if interval not in INTERVAL_TO_DELTA:
                raise ValueError(f"Invalid interval: {interval}")

            stock = yf.Ticker(symbol)
            now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

            # Buffer: Fetch 2x + 10 to account for weekends/holidays/gaps
            buffer_factor = 2.5 if interval in ["1d", "1wk", "1mo"] else 4.0
            start_date = now - (INTERVAL_TO_DELTA[interval] * int(no_of_candles * buffer_factor + 10))
        
            # yfinance history end is exclusive
            df = stock.history(interval=interval, start=start_date, end=now)

            if df.empty:
                logging.warning(f"No data found for symbol: {symbol}")
                return None

            # Ensure we only have the requested number of most recent candles
            df = df.tail(no_of_candles)
        
            candles = []
            for ts, row in df.iterrows():
                candles.append({
                    "symbol": symbol,
                    "open": _to_number(row["Open"]),
                    "high": _to_number(row["High"]),
                    "low": _to_number(row["Low"]),
                    "close": _to_number(row["Close"]),
                    "volume": _to_number(row["Volume"], is_int=True),
                    "timestamp": _normalize_timestamp(ts.to_pydatetime()),
                })

            if field == "all":
                return candles
            elif field in {"open", "high", "low", "close", "volume"}:
                return [candle[field] for candle in candles]
            else:
                raise ValueError(f"Invalid field: {field}")

        except Exception as e:
            logging.error(f"Error fetching data for symbol {symbol}: {e}")
            return None


# -------------------------------------------------
# Trading Actions API
# -------------------------------------------------

class action:
    @staticmethod
    async def buy(quantity: int, price=None, symbol: str = SYMBOL):
        return await action._send("buy", symbol, quantity, price)

    @staticmethod
    async def sell(quantity: int, price=None, symbol: str = SYMBOL):
        return await action._send("sell", symbol, quantity, price)

    @staticmethod
    async def _send(action_type, symbol, quantity, price):
        if not isinstance(symbol, str) or not symbol:
            return _error("INVALID_SYMBOL")

        if not isinstance(quantity, int) or quantity <= 0:
            return _error("INVALID_QUANTITY")

        if price is not None and (not isinstance(price, (int, float)) or price <= 0):
            return _error("INVALID_PRICE")

        payload = {
            "strategy_id": STRATEGY_ID,
            "symbol": symbol,
            "action": action_type,
            "quantity": quantity,
            "price": price,
            "ts": _now_s()
        }

        try:
            await _socket.send_json(payload)
            response = await _socket.recv_json()
        except zmq.error.Again:
            logger.error("Trade adapter send timeout")
            return _error("ENGINE_UNAVAILABLE")
        except Exception as e:
            logger.exception("IPC failure")
            return _error("IPC_ERROR", str(e))

        if not isinstance(response, dict):
            return _error("INVALID_RESPONSE")

        return response
