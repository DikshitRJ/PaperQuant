from Candle_fetcher import candle_list
import pandas as pd
import numpy as np

# Moving averages are technical indicators used to smooth out price data over a specific period.
# They help identify trends by filtering out short-term fluctuations.

def _wma_series(series, period):
    if len(series) < period:
        return pd.Series([np.nan] * len(series))
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def sma(symbol, period, interval):
    """
    Calculate Simple Moving Average (SMA).
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None
    return pd.Series(candles).mean()

def ema(symbol, period, interval):
    """
    Calculate Exponential Moving Average (EMA).
    """
    # Use 3x period for EMA warm-up
    candles = candle_list(symbol, period * 3, interval, field="close")
    if not candles:
        return None
    return pd.Series(candles).ewm(span=period, adjust=False).mean().iloc[-1]

def wma(symbol, period, interval):
    """
    Calculate Weighted Moving Average (WMA).
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles or len(candles) < period:
        return None
    
    series = pd.Series(candles)
    return _wma_series(series, period).iloc[-1]

def hma(symbol, period, interval):
    """
    Calculate Hull Moving Average (HMA).
    """
    # HMA needs more data for the nested WMAs
    candles = candle_list(symbol, period + int(period**0.5) + 10, interval, field="close")
    if not candles:
        return None
    
    series = pd.Series(candles)
    half_period = period // 2
    sqrt_period = int(np.sqrt(period))
    
    wma_half = _wma_series(series, half_period)
    wma_full = _wma_series(series, period)
    
    diff = 2 * wma_half - wma_full
    hma_series = _wma_series(diff.dropna(), sqrt_period)
    
    return hma_series.iloc[-1]

def cma(symbol, period, interval):
    """
    Calculate Cumulative Moving Average (CMA).
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None
    return pd.Series(candles).expanding().mean().iloc[-1]

def tma(symbol, period, interval):
    """
    Calculate Triangular Moving Average (TMA).
    """
    # TMA is SMA of SMA, requires ~2x period
    candles = candle_list(symbol, period * 2, interval, field="close")
    if not candles:
        return None
        
    sma1 = pd.Series(candles).rolling(window=period).mean()
    tma_series = sma1.rolling(window=period).mean()
    return tma_series.iloc[-1]

def ama(symbol, period, interval, fast=2, slow=30):
    """
    Calculate Kaufman's Adaptive Moving Average (KAMA).
    """
    candles = candle_list(symbol, period + 30, interval, field="close")
    if not candles:
        return None
        
    series = pd.Series(candles)
    change = (series - series.shift(period)).abs()
    volatility = (series - series.shift(1)).abs().rolling(period).sum()
    er = change / volatility
    
    sc_fast = 2 / (fast + 1)
    sc_slow = 2 / (slow + 1)
    sc = (er * (sc_fast - sc_slow) + sc_slow) ** 2
    
    ama_val = pd.Series(index=series.index, dtype='float64')
    # Start with an SMA or first close
    ama_val.iloc[period-1] = series.iloc[period-1]
    
    for i in range(period, len(series)):
        ama_val.iloc[i] = ama_val.iloc[i-1] + sc.iloc[i] * (series.iloc[i] - ama_val.iloc[i-1])
        
    return ama_val.iloc[-1]

def macd(symbol, short_period, long_period, signal_period, interval):
    """
    Calculate Moving Average Convergence Divergence (MACD).
    """
    # MACD needs significant warm-up
    candles = candle_list(symbol, long_period * 3 + signal_period, interval, field="close")
    if not candles:
        return None

    series = pd.Series(candles)
    short_ema = series.ewm(span=short_period, adjust=False).mean()
    long_ema = series.ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    return {
        "macd": macd_line.iloc[-1],
        "signal": signal_line.iloc[-1],
        "histogram": macd_line.iloc[-1] - signal_line.iloc[-1]
    }
