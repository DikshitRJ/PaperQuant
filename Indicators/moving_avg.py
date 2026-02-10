from Candle_fetcher import candle_list
import pandas as pd

# Moving averages are technical indicators used to smooth out price data over a specific period.
# They help identify trends by filtering out short-term fluctuations.

def sma(symbol, period, interval):
    """
    Calculate Simple Moving Average (SMA).
    SMA is the unweighted mean of the previous n data points.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the SMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the SMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None
    sma_value = pd.Series(candles).mean()
    return sma_value

def ema(symbol, period, interval):
    """
    Calculate Exponential Moving Average (EMA).
    EMA gives more weight to recent prices, making it more responsive to new data.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the EMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the EMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None
    ema_value = pd.Series(candles).ewm(span=period, adjust=False).mean().iloc[-1]
    return ema_value

def wma(symbol, period, interval):
    """
    Calculate Weighted Moving Average (WMA).
    WMA assigns more weight to recent data points, reducing the lag compared to SMA.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the WMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the WMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None

    weights = pd.Series(range(1, period + 1))
    wma_value = (pd.Series(candles).iloc[-period:] * weights).sum() / weights.sum()
    return wma_value

def hma(symbol, period, interval):
    """
    Calculate Hull Moving Average (HMA).
    HMA reduces lag and improves smoothness by using weighted moving averages.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the HMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the HMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None

    half_length = int(period / 2)
    sqrt_length = int(period ** 0.5)

    half_wma = wma(symbol, half_length, interval)
    full_wma = wma(symbol, period, interval)

    if half_wma is None or full_wma is None:
        return None

    diff_wma = 2 * half_wma - full_wma
    hma_value = wma(symbol, sqrt_length, interval)
    return hma_value

def cma(symbol, period, interval):
    """
    Calculate Cumulative Moving Average (CMA).
    CMA considers all data points up to the current point, smoothing long-term trends.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the CMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the CMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None

    cma_value = pd.Series(candles).expanding().mean().iloc[-1]
    return cma_value

def tma(symbol, period, interval):
    """
    Calculate Triangular Moving Average (TMA).
    TMA is a double-smoothed SMA, giving more weight to the middle of the data set.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the TMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Numerical value of the TMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None

    sma_values = pd.Series(candles).rolling(window=period).mean()
    tma_value = sma_values.rolling(window=period).mean().iloc[-1]
    return tma_value

def ama(symbol, period, interval, fast=2, slow=30):
    """
    Calculate Adaptive Moving Average (AMA).
    AMA adjusts its sensitivity based on market volatility, making it adaptive to trends.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the AMA.
    :param interval: Interval for the candle data (e.g., "1d").
    :param fast: Fast EMA smoothing constant.
    :param slow: Slow EMA smoothing constant.
    :return: Numerical value of the AMA.
    """
    candles = candle_list(symbol, period, interval, field="close")
    if not candles:
        return None

    ema_fast = pd.Series(candles).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(candles).ewm(span=slow, adjust=False).mean()
    ama_value = (ema_fast + ema_slow) / 2
    return ama_value.iloc[-1]

def macd(symbol, short_period, long_period, signal_period, interval):
    """
    Calculate Moving Average Convergence Divergence (MACD).
    MACD is the difference between two EMAs (short and long) and a signal line.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param short_period: Short EMA period (e.g., 12).
    :param long_period: Long EMA period (e.g., 26).
    :param signal_period: Signal line EMA period (e.g., 9).
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Tuple of (MACD value, Signal line value).
    """
    candles = candle_list(symbol, long_period, interval, field="close")
    if not candles:
        return None

    short_ema = pd.Series(candles).ewm(span=short_period, adjust=False).mean()
    long_ema = pd.Series(candles).ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line.iloc[-1], signal_line.iloc[-1]

