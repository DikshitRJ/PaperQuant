from Candle_fetcher import candle_list
import pandas as pd
import numpy as np

def rsi(symbol, period, interval):
    """
    Calculate Relative Strength Index (RSI).
    """
    # Use 3x period for warm-up
    close = pd.Series(
        candle_list(symbol, period * 3, interval, field="close"),
        dtype="float64"
    )
    if close.empty: return None

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series.iloc[-1] if not rsi_series.dropna().empty else None

def stochastic_oscillator(symbol, period, interval, k_period=14, smooth_k=3, smooth_d=3):
    """
    Calculate Stochastic Oscillator.
    """
    candles = candle_list(symbol, period + k_period + 10, interval, field="all")
    if not candles: return None

    high = pd.Series([c["high"] for c in candles], dtype="float64")
    low = pd.Series([c["low"] for c in candles], dtype="float64")
    close = pd.Series([c["close"] for c in candles], dtype="float64")

    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()

    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_k_smoothed = percent_k.rolling(smooth_k).mean()
    percent_d = percent_k_smoothed.rolling(smooth_d).mean()

    return {
        "k": percent_k_smoothed.iloc[-1],
        "d": percent_d.iloc[-1]
    }

def stochastic_rsi(symbol, period, interval, rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3):
    """
    Calculate Stochastic RSI.
    """
    # Fetch enough for RSI warm-up + Stochastic rolling window
    candles = candle_list(symbol, (rsi_period * 3) + stoch_period + 10, interval, field="close")
    if not candles: return None
    
    close = pd.Series(candles)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / rsi_period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))

    min_rsi = rsi_series.rolling(stoch_period).min()
    max_rsi = rsi_series.rolling(stoch_period).max()

    stoch_rsi_val = 100 * (rsi_series - min_rsi) / (max_rsi - min_rsi)
    percent_k = stoch_rsi_val.rolling(smooth_k).mean()
    percent_d = percent_k.rolling(smooth_d).mean()

    return {
        "k": percent_k.iloc[-1],
        "d": percent_d.iloc[-1]
    }

def cci(symbol, period, interval, cci_period=20):
    """
    Calculate Commodity Channel Index (CCI).
    """
    candles = candle_list(symbol, period + cci_period + 10, interval, field="all")
    if not candles: return None

    high = pd.Series([c["high"] for c in candles], dtype="float64")
    low = pd.Series([c["low"] for c in candles], dtype="float64")
    close = pd.Series([c["close"] for c in candles], dtype="float64")

    tp = (high + low + close) / 3
    sma = tp.rolling(cci_period).mean()
    mad = tp.rolling(cci_period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)

    cci_val = (tp - sma) / (0.015 * mad)
    return cci_val.iloc[-1]

def williams_r(symbol, period, interval, will_period=14):
    """
    Calculate Williams %R.
    """
    candles = candle_list(symbol, period + will_period + 10, interval, field="all")
    if not candles: return None

    high = pd.Series([c["high"] for c in candles], dtype="float64")
    low = pd.Series([c["low"] for c in candles], dtype="float64")
    close = pd.Series([c["close"] for c in candles], dtype="float64")

    highest_high = high.rolling(will_period).max()
    lowest_low = low.rolling(will_period).min()

    wr = -100 * (highest_high - close) / (highest_high - lowest_low)
    return wr.iloc[-1]

def roc(symbol, period, interval, roc_period=12):
    """
    Calculate Rate of Change (ROC).
    """
    close = pd.Series(candle_list(symbol, period + roc_period + 5, interval, field="close"), dtype="float64")
    if close.empty: return None

    roc_val = ((close - close.shift(roc_period)) / close.shift(roc_period)) * 100
    return roc_val.iloc[-1]

def tsi(symbol, period, interval, long=25, short=13):
    """
    Calculate True Strength Index (TSI).
    """
    close = pd.Series(candle_list(symbol, period + long + short + 20, interval, field="close"), dtype="float64")
    if close.empty: return None

    delta = close.diff()
    ema1 = delta.ewm(span=short, adjust=False).mean()
    ema2 = ema1.ewm(span=long, adjust=False).mean()

    abs_delta = delta.abs()
    abs_ema1 = abs_delta.ewm(span=short, adjust=False).mean()
    abs_ema2 = abs_ema1.ewm(span=long, adjust=False).mean()

    tsi_val = 100 * (ema2 / abs_ema2)
    return tsi_val.iloc[-1]

def ultimate_oscillator(symbol, period, interval, short=7, medium=14, long=28):
    """
    Calculate Ultimate Oscillator.
    """
    candles = candle_list(symbol, period + long + 10, interval, field="all")
    if not candles: return None

    high = pd.Series([c["high"] for c in candles], dtype="float64")
    low = pd.Series([c["low"] for c in candles], dtype="float64")
    close = pd.Series([c["close"] for c in candles], dtype="float64")

    prev_close = close.shift(1)
    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = pd.concat([high, prev_close], axis=1).max(axis=1) - pd.concat([low, prev_close], axis=1).min(axis=1)

    avg1 = bp.rolling(short).sum() / tr.rolling(short).sum()
    avg2 = bp.rolling(medium).sum() / tr.rolling(medium).sum()
    avg3 = bp.rolling(long).sum() / tr.rolling(long).sum()

    uo = 100 * ((4 * avg1) + (2 * avg2) + avg3) / 7
    return uo.iloc[-1]

def ppo(symbol, period, interval, fast=12, slow=26, signal=9):
    """
    Calculate Percentage Price Oscillator (PPO).
    """
    close = pd.Series(candle_list(symbol, period + (slow * 3), interval, field="close"), dtype="float64")
    if close.empty: return None

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    ppo_line = (ema_fast - ema_slow) / ema_slow * 100
    signal_line = ppo_line.ewm(span=signal, adjust=False).mean()
    
    return {
        "ppo": ppo_line.iloc[-1],
        "signal": signal_line.iloc[-1],
        "histogram": ppo_line.iloc[-1] - signal_line.iloc[-1]
    }
