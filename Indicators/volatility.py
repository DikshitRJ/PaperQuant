from Candle_fetcher import candle_list
import pandas as pd

# Volatility indicators measure the degree of variation in price movements.
# Examples include ATR, Bollinger Bands, Chaikin Volatility, etc.

def atr(symbol, period, interval):
    """
    Calculate the Average True Range (ATR).
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for the ATR calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: ATR value.
    """
    candles = candle_list(symbol, period + 1, interval, field="all")
    if not candles:
        return None
        
    high = pd.Series([c["high"] for c in candles])
    low = pd.Series([c["low"] for c in candles])
    close = pd.Series([c["close"] for c in candles])
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_value = tr.rolling(window=period).mean().iloc[-1]
    return atr_value

def bollinger_bands(symbol, period, interval, multiplier=2):
    """
    Calculate Bollinger Bands.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for the Bollinger Bands calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param multiplier: Multiplier for the standard deviation (default: 2).
    :return: Dictionary with upper, middle, and lower bands.
    """
    close = candle_list(symbol, period, interval, field="close")
    if not close:
        return None
        
    close_ser = pd.Series(close)
    middle_band = close_ser.rolling(window=period).mean()
    std_dev = close_ser.rolling(window=period).std()
    upper_band = middle_band + (multiplier * std_dev)
    lower_band = middle_band - (multiplier * std_dev)
    
    return {
        "upper": upper_band.iloc[-1],
        "middle": middle_band.iloc[-1],
        "lower": lower_band.iloc[-1]
    }
