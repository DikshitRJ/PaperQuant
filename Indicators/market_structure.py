from .Candle_fetcher import candle_list
import pandas as pd
import numpy as np

# Market structure indicators describe higher-level price behavior.
# Examples include Swing High/Low Detection, Market Regime, Choppiness Index, etc.

def swing_high_low(symbol, period, interval):
    """
    Detect the last swing high and low over a rolling window.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Tuple of last identified swing high and swing low values.
    """
    # Fetch extra data to find peaks/troughs that are fully formed
    prices = candle_list(symbol, period + 20, interval, field="close")
    if not prices:
        return None, None
        
    series = pd.Series(prices)
    # Using center=True finds peaks in the middle of a window.
    # To avoid NaNs at the end, we look for the last non-NaN value.
    swing_highs = series.rolling(window=period, center=True).max()
    swing_lows = series.rolling(window=period, center=True).min()
    
    # Filter for values that are actual local peaks/troughs
    last_high = swing_highs.dropna().iloc[-1] if not swing_highs.dropna().empty else None
    last_low = swing_lows.dropna().iloc[-1] if not swing_lows.dropna().empty else None
    
    return last_high, last_low

def choppiness_index(symbol, period, interval):
    """
    Calculate the Choppiness Index.
    """
    # Fetch period + 1 to account for the first True Range NaN
    candles = candle_list(symbol, period + 1, interval, field="all")
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
    
    price_range = range_high - range_low
    # Avoid division by zero
    if price_range.iloc[-1] == 0 or pd.isna(price_range.iloc[-1]):
        return 50.0  # Return neutral value if no range
        
    # Calculate chop
    chop = 100 * np.log10(sum_tr / price_range) / np.log10(period)
    
    return chop.iloc[-1] if not pd.isna(chop.iloc[-1]) else None
