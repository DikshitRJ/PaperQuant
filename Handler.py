import os
import sys
import zmq
import time
import logging
from diskcache import Cache
from datetime import datetime, timezone

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

# -------------------------------------------------
# ZMQ DEALER setup
# -------------------------------------------------

_context = zmq.Context.instance()
_socket = _context.socket(zmq.DEALER)

# Explicit identity for ROUTER
_socket.setsockopt(zmq.IDENTITY, STRATEGY_ID.encode())

_socket.setsockopt(zmq.RCVTIMEO, 2000)
_socket.setsockopt(zmq.SNDTIMEO, 2000)

_socket.connect(ZMQ_ENDPOINT)

# -------------------------------------------------
# Cache (read-only from Handler POV)
# -------------------------------------------------

_cache = Cache(CACHE_PATH)

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
    return time.time_s()
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
        if ts is not None:
            try:
                ts = _normalize_timestamp(ts).timestamp()  # Convert to nanoseconds
            except Exception as e:
                logger.error(f"Failed to normalize timestamp: {e}")
                return _error("INVALID_TIMESTAMP")

            age = _now_s() - ts
            if age > 60:  # 5 seconds
                return _error("STALE_DATA", "Price data is stale")

        return _ok(candle)

# -------------------------------------------------
# Trading Actions API
# -------------------------------------------------

class action:
    @staticmethod
    def buy(quantity: int, price=None, symbol: str = SYMBOL):
        return action._send("buy", symbol, quantity, price)

    @staticmethod
    def sell(quantity: int, price=None, symbol: str = SYMBOL):
        return action._send("sell", symbol, quantity, price)

    @staticmethod
    def _send(action_type, symbol, quantity, price):
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
            _socket.send_json(payload)
            response = _socket.recv_json()
        except zmq.error.Again:
            logger.error("Trade adapter timeout")
            return _error("ENGINE_UNAVAILABLE")
        except Exception as e:
            logger.exception("IPC failure")
            return _error("IPC_ERROR", str(e))

        if not isinstance(response, dict):
            return _error("INVALID_RESPONSE")

        return response
