import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
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
            'open': latest_candle['Open'],
            'high': latest_candle['High'],
            'low': latest_candle['Low'],
            'close': latest_candle['Close'],
            'volume': latest_candle['Volume'],
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
                    'open': latest_candle['Open'],
                    'high': latest_candle['High'],
                    'low': latest_candle['Low'],
                    'close': latest_candle['Close'],
                    'volume': latest_candle['Volume'],
                    'timestamp': latest_candle.name.to_pydatetime()
                }
            except KeyError:
                logging.warning(f"No data found for symbol: {symbol}")

        return data

    except Exception as e:
        logging.error(f"Error fetching data for symbols {symbols}: {e}")
        return {}