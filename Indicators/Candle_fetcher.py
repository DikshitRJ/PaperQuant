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
