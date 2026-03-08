from .Candle_fetcher import candle_list
import pandas as pd

# Volume-based indicators analyze the amount of traded volume to understand market strength.
# Examples include OBV, Accumulation/Distribution Line, Chaikin Money Flow, etc.

def obv(symbol, period, interval):
    """
    Calculate the On-Balance Volume (OBV).
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: OBV value.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    close_ser = pd.Series([c["close"] for c in candles])
    volume_ser = pd.Series([c["volume"] for c in candles])
    
    diff = close_ser.diff()
    direction = pd.Series(0, index=close_ser.index)
    direction[diff > 0] = 1
    direction[diff < 0] = -1
    
    obv_value = (direction * volume_ser).cumsum().iloc[-1]
    return obv_value

def ad_line(symbol, period, interval):
    """
    Calculate the Accumulation/Distribution Line.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: A/D Line value.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high_ser = pd.Series([c["high"] for c in candles])
    low_ser = pd.Series([c["low"] for c in candles])
    close_ser = pd.Series([c["close"] for c in candles])
    volume_ser = pd.Series([c["volume"] for c in candles])
    
    mfm = ((close_ser - low_ser) - (high_ser - close_ser)) / (high_ser - low_ser)
    mfm = mfm.fillna(0)
    mfv = mfm * volume_ser
    adl = mfv.cumsum().iloc[-1]
    return adl
