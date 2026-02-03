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


def current_candle(symbol, interval="1m", lookback_minutes=3):
    try:
        stock = yf.Ticker(symbol)

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        end = now - timedelta(minutes=1)
        start = end - timedelta(minutes=lookback_minutes - 1)

        df = stock.history(interval=interval, start=start, end=end)

        if df.empty:
            logging.warning(f"No data found for symbol: {symbol}")
            return None

        # Drop any candle that is newer than `end`
        df = df[df.index <= end]

        if df.empty:
            return None

        latest_candle = df.iloc[-1]
        ts = _normalize_timestamp(latest_candle.name.to_pydatetime())

        return {
            "symbol": symbol,
            "open": _to_number(latest_candle["Open"]),
            "high": _to_number(latest_candle["High"]),
            "low": _to_number(latest_candle["Low"]),
            "close": _to_number(latest_candle["Close"]),
            "volume": _to_number(latest_candle["Volume"], is_int=True),
            "timestamp": ts,
        }

    except Exception as e:
        logging.error(f"Error fetching data for symbol {symbol}: {e}")
        return None


def fetch_multiple_candles(symbols, interval="1m", lookback_minutes=3):
    try:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        end = now - timedelta(minutes=1)
        start = end - timedelta(minutes=lookback_minutes - 1)

        stocks = yf.Tickers(" ".join(symbols))
        df = stocks.download(interval=interval, start=start, end=end)

        if df.empty:
            logging.warning("No data found for the given symbols.")
            return {}

        data = {}

        for symbol in symbols:
            try:
                symbol_df = df.xs(symbol, level=1, axis=1)

                # Drop candles newer than `end`
                symbol_df = symbol_df[symbol_df.index <= end]

                if symbol_df.empty:
                    continue

                latest_candle = symbol_df.iloc[-1]
                ts = _normalize_timestamp(latest_candle.name.to_pydatetime())

                data[symbol] = {
                    "symbol": symbol,
                    "open": _to_number(latest_candle["Open"]),
                    "high": _to_number(latest_candle["High"]),
                    "low": _to_number(latest_candle["Low"]),
                    "close": _to_number(latest_candle["Close"]),
                    "volume": _to_number(latest_candle["Volume"], is_int=True),
                    "timestamp": ts,
                }

            except KeyError:
                logging.warning(f"No data found for symbol: {symbol}")

        return data

    except Exception as e:
        logging.error(f"Error fetching data for symbols {symbols}: {e}")
        return {}
