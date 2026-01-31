# ...existing code...
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

def _to_number(val, is_int=False):
    if pd.isna(val):
        return None
    try:
        if is_int:
            return int(val)
        return float(val)
    except Exception:
        try:
            return float(val)
        except Exception:
            return None

def current_candle(symbol, interval='1m'):
    try:
        stock = yf.Ticker(symbol)
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=3)
        df = stock.history(interval=interval, start=start_time, end=end_time)

        if df.empty:
            logging.warning(f"No data found for symbol: {symbol}")
            return None

        latest_candle = df.iloc[-1]
        candle_data = {
            'symbol': symbol,
            'open': _to_number(latest_candle['Open']),
            'high': _to_number(latest_candle['High']),
            'low': _to_number(latest_candle['Low']),
            'close': _to_number(latest_candle['Close']),
            'volume': _to_number(latest_candle['Volume'], is_int=True),
            'timestamp': latest_candle.name.to_pydatetime()
        }
        return candle_data

    except Exception as e:
        logging.error(f"Error fetching data for symbol {symbol}: {e}")
        return None

def fetch_multiple_candles(symbols, interval='1m', lookback_minutes=3):
    try:
        # Calculate the time range
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Fetch data for multiple stocks using .download()
        stocks = yf.Tickers(" ".join(symbols))
        df = stocks.download(interval=interval, start=start_time, end=end_time)

        if df.empty:
            logging.warning("No data found for the given symbols.")
            return {}

        # Process the data for each symbol
        data = {}
        for symbol in symbols:
            try:
                # Extract data for the symbol from the MultiIndex DataFrame
                symbol_data = df.xs(symbol, level=1, axis=1)
                latest_candle = symbol_data.iloc[-1]
                data[symbol] = {
                    'symbol': symbol,
                    'open': _to_number(latest_candle['Open']),
                    'high': _to_number(latest_candle['High']),
                    'low': _to_number(latest_candle['Low']),
                    'close': _to_number(latest_candle['Close']),
                    'volume': _to_number(latest_candle['Volume'], is_int=True),
                    'timestamp': latest_candle.name.to_pydatetime()
                }
            except KeyError:
                logging.warning(f"No data found for symbol: {symbol}")

        return data

    except Exception as e:
        logging.error(f"Error fetching data for symbols {symbols}: {e}")
        return {}