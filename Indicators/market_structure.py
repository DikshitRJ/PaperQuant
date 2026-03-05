from Candle_fetcher import candle_list
import pandas as pd
import numpy as np

# Market structure indicators describe higher-level price behavior.
# Examples include Swing High/Low Detection, Market Regime, Choppiness Index, etc.

def swing_high_low(symbol, period, interval):
    """
    Detect swing highs and lows over a rolling window.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Tuple of swing high and swing low values.
    """
    prices = candle_list(symbol, period, interval, field="close")
    if not prices:
        return None
        
    swing_high = pd.Series(prices).rolling(window=period, center=True).max().iloc[-1]
    swing_low = pd.Series(prices).rolling(window=period, center=True).min().iloc[-1]
    return swing_high, swing_low

def choppiness_index(symbol, period, interval):
    """
    Calculate the Choppiness Index.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation (default 14 in many platforms, but we use 'period').
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Choppiness Index value.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high_ser = pd.Series([c["high"] for c in candles])
    low_ser = pd.Series([c["low"] for c in candles])
    close_ser = pd.Series([c["close"] for c in candles])
    
    tr1 = high_ser - low_ser
    tr2 = (high_ser - close_ser.shift(1)).abs()
    tr3 = (low_ser - close_ser.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    sum_tr = tr.rolling(window=period).sum()
    range_high = high_ser.rolling(window=period).max()
    range_low = low_ser.rolling(window=period).min()
    
    chop = 100 * np.log10(sum_tr / (range_high - range_low)) / np.log10(period)
    return chop.iloc[-1]
