import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
import logging


def _to_number(val, is_int=False):
    if pd.isna(val):
        return None
    try:
        return int(val) if is_int else float(val)
    except Exception:
        return None


def _normalize_timestamp(ts):
    """
    Force UTC, minute-aligned timestamp.
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    return ts.replace(second=0, microsecond=0)


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

def candle_list(symbol, no_of_candles, interval, field="all"):
    try:
        if interval not in INTERVAL_TO_DELTA:
            raise ValueError(f"Invalid interval: {interval}")

        stock = yf.Ticker(symbol)

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        # yfinance candles are closed candles → exclude current forming candle
        end = now - INTERVAL_TO_DELTA[interval]
        start = end - INTERVAL_TO_DELTA[interval] * (no_of_candles - 1)

        df = stock.history(interval=interval, start=start, end=end)

        if df.empty:
            logging.warning(f"No data found for symbol: {symbol}")
            return None

        df = df[df.index <= end]

        if df.empty:
            return None
        
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