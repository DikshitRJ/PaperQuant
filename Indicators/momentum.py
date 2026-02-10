from Candle_fetcher import candle_list
import pandas as pd
import numpy as np



def rsi(symbol, period, interval):
    """
    Calculate Relative Strength Index (RSI).
    RSI measures the speed and change of price movements, indicating overbought or oversold conditions.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the RSI calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: RSI values as a pandas Series.
    """
    close = pd.Series(
        candle_list(symbol, period, interval, field="close"),
        dtype="float64"
    )

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def stochastic_oscillator(
    symbol,
    period,
    interval,
    k_period=14,
    smooth_k=3,
    smooth_d=3
):
    """
    Calculate Stochastic Oscillator.
    The Stochastic Oscillator compares a particular closing price to a range of prices over a period of time.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param k_period: Number of periods for %K calculation.
    :param smooth_k: Smoothing factor for %K.
    :param smooth_d: Smoothing factor for %D.
    :return: %K and %D values as pandas Series.
    """
    candles = candle_list(symbol, period, interval, field="all")

    high = pd.Series([c.high for c in candles], dtype="float64")
    low = pd.Series([c.low for c in candles], dtype="float64")
    close = pd.Series([c.close for c in candles], dtype="float64")

    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()

    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_k = percent_k.rolling(smooth_k).mean()
    percent_d = percent_k.rolling(smooth_d).mean()

    return percent_k, percent_d


def stochastic_rsi(
    symbol,
    period,
    interval,
    rsi_period=14,
    stoch_period=14,
    smooth_k=3,
    smooth_d=3
):
    """
    Calculate Stochastic RSI.
    Stochastic RSI applies the Stochastic Oscillator formula to RSI values instead of price data.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param rsi_period: Number of periods for RSI calculation.
    :param stoch_period: Number of periods for Stochastic calculation.
    :param smooth_k: Smoothing factor for %K.
    :param smooth_d: Smoothing factor for %D.
    :return: %K and %D values as pandas Series.
    """
    rsi_series = rsi(symbol, period, interval, rsi_period)

    min_rsi = rsi_series.rolling(stoch_period).min()
    max_rsi = rsi_series.rolling(stoch_period).max()

    stoch_rsi = 100 * (rsi_series - min_rsi) / (max_rsi - min_rsi)

    percent_k = stoch_rsi.rolling(smooth_k).mean()
    percent_d = percent_k.rolling(smooth_d).mean()

    return percent_k, percent_d


def cci(symbol, period, interval, cci_period=20):
    """
    Calculate Commodity Channel Index (CCI).
    CCI measures the deviation of the price from its average price over a period.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param cci_period: Number of periods for the CCI calculation.
    :return: CCI values as a pandas Series.
    """
    candles = candle_list(symbol, period, interval, field="all")

    high = pd.Series([c.high for c in candles], dtype="float64")
    low = pd.Series([c.low for c in candles], dtype="float64")
    close = pd.Series([c.close for c in candles], dtype="float64")

    tp = (high + low + close) / 3
    sma = tp.rolling(cci_period).mean()
    mad = tp.rolling(cci_period).apply(
        lambda x: np.mean(np.abs(x - x.mean())),
        raw=True
    )

    return (tp - sma) / (0.015 * mad)


def williams_r(symbol, period, interval, will_period=14):
    """
    Calculate Williams %R.
    Williams %R measures overbought and oversold levels, similar to the Stochastic Oscillator.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param will_period: Number of periods for the Williams %R calculation.
    :return: Williams %R values as a pandas Series.
    """
    candles = candle_list(symbol, period, interval, field="all")

    high = pd.Series([c.high for c in candles], dtype="float64")
    low = pd.Series([c.low for c in candles], dtype="float64")
    close = pd.Series([c.close for c in candles], dtype="float64")

    highest_high = high.rolling(will_period).max()
    lowest_low = low.rolling(will_period).min()

    return -100 * (highest_high - close) / (highest_high - lowest_low)


def roc(symbol, period, interval, roc_period=12):
    """
    Calculate Rate of Change (ROC).
    ROC measures the percentage change in price over a specified period.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param roc_period: Number of periods for the ROC calculation.
    :return: ROC values as a pandas Series.
    """
    close = pd.Series(
        candle_list(symbol, period, interval, field="close"),
        dtype="float64"
    )

    return ((close - close.shift(roc_period)) / close.shift(roc_period)) * 100


def tsi(symbol, period, interval, long=25, short=13):
    """
    Calculate True Strength Index (TSI).
    TSI measures the strength of a trend by smoothing price momentum.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param long: Long smoothing period.
    :param short: Short smoothing period.
    :return: TSI values as a pandas Series.
    """
    close = pd.Series(
        candle_list(symbol, period, interval, field="close"),
        dtype="float64"
    )

    delta = close.diff()

    ema1 = delta.ewm(span=short, adjust=False).mean()
    ema2 = ema1.ewm(span=long, adjust=False).mean()

    abs_delta = delta.abs()
    abs_ema1 = abs_delta.ewm(span=short, adjust=False).mean()
    abs_ema2 = abs_ema1.ewm(span=long, adjust=False).mean()

    return 100 * (ema2 / abs_ema2)


def ultimate_oscillator(
    symbol,
    period,
    interval,
    short=7,
    medium=14,
    long=28
):
    """
    Calculate Ultimate Oscillator.
    The Ultimate Oscillator combines short, medium, and long-term price action to measure momentum.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param short: Short-term period.
    :param medium: Medium-term period.
    :param long: Long-term period.
    :return: Ultimate Oscillator values as a pandas Series.
    """
    candles = candle_list(symbol, period, interval, field="all")

    high = pd.Series([c.high for c in candles], dtype="float64")
    low = pd.Series([c.low for c in candles], dtype="float64")
    close = pd.Series([c.close for c in candles], dtype="float64")

    prev_close = close.shift(1)

    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = (
        pd.concat([high, prev_close], axis=1).max(axis=1)
        - pd.concat([low, prev_close], axis=1).min(axis=1)
    )

    avg1 = bp.rolling(short).sum() / tr.rolling(short).sum()
    avg2 = bp.rolling(medium).sum() / tr.rolling(medium).sum()
    avg3 = bp.rolling(long).sum() / tr.rolling(long).sum()

    return 100 * ((4 * avg1) + (2 * avg2) + avg3) / 7


def ppo(symbol, period, interval, fast=12, slow=26, signal=9):
    """
    Calculate Percentage Price Oscillator (PPO).
    PPO measures the difference between two EMAs as a percentage of the larger EMA.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of periods for the calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :param fast: Fast EMA period.
    :param slow: Slow EMA period.
    :param signal: Signal line EMA period.
    :return: PPO line, signal line, and histogram as pandas Series.
    """
    close = pd.Series(
        candle_list(symbol, period, interval, field="close"),
        dtype="float64"
    )

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    ppo_line = (ema_fast - ema_slow) / ema_slow * 100
    signal_line = ppo_line.ewm(span=signal, adjust=False).mean()
    histogram = ppo_line - signal_line

    return ppo_line, signal_line, histogram
