from .Candle_fetcher import candle_list
import pandas as pd

# Support and resistance indicators calculate key price levels.
# Examples include Pivot Points, Fibonacci Retracements, Rolling High/Low, etc.

def pivot_points(symbol, period, interval):
    """
    Calculate Pivot Points (Classic formula).
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation (usually 1 for daily pivot).
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Dictionary with pivot point, support, and resistance levels.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high = candles[-1]["high"]
    low = candles[-1]["low"]
    close = candles[-1]["close"]
    
    pivot = (high + low + close) / 3
    support1 = (2 * pivot) - high
    resistance1 = (2 * pivot) - low
    return {"pivot": pivot, "support1": support1, "resistance1": resistance1}

def rolling_high_low(symbol, period, interval):
    """
    Calculate rolling high and low over a specified window.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Dictionary of rolling high and rolling low.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    prices = [c["close"] for c in candles]
    rolling_high = pd.Series(prices).rolling(window=period).max()
    rolling_low = pd.Series(prices).rolling(window=period).min()
    return {"high": rolling_high.iloc[-1], "low": rolling_low.iloc[-1]}

def fib_retracement(symbol, period, interval, level):
    """
    Calculate a specific Fibonacci Retracement level for a given period.
    :param symbol: Stock symbol.
    :param period: Rolling window to find swing high/low.
    :param interval: Data interval.
    :param level: The Fibonacci level (e.g., 0.382, 0.618).
    :return: Price value at the specified level.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high = max(c["high"] for c in candles)
    low = min(c["low"] for c in candles)
    diff = high - low
    
    return high - (level * diff)

def fib_extension(symbol, period, interval, level):
    """
    Calculate a specific Fibonacci Extension level for a given period.
    :param symbol: Stock symbol.
    :param period: Rolling window to find swing high/low.
    :param interval: Data interval.
    :param level: The Fibonacci extension level (e.g., 1.618).
    :return: Price value at the specified extension level.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high = max(c["high"] for c in candles)
    low = min(c["low"] for c in candles)
    diff = high - low
    
    return high + ((level - 1.0) * diff)
