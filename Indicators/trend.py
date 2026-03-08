from .Candle_fetcher import candle_list
import pandas as pd

# Trend indicators identify the direction and strength of a market trend.
# Examples include ADX, DMI, Parabolic SAR, Supertrend, etc.

def adx(symbol, period, interval):
    """
    Calculate the Average Directional Index (ADX).
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: ADX value.
    """
    candles = candle_list(symbol, period * 2, interval, field="all")
    if not candles:
        return None
        
    high_ser = pd.Series([c["high"] for c in candles])
    low_ser = pd.Series([c["low"] for c in candles])
    close_ser = pd.Series([c["close"] for c in candles])
    
    tr1 = high_ser - low_ser
    tr2 = (high_ser - close_ser.shift(1)).abs()
    tr3 = (low_ser - close_ser.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    up_move = high_ser - high_ser.shift(1)
    down_move = low_ser.shift(1) - low_ser
    
    plus_dm = pd.Series(0.0, index=high_ser.index)
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    
    minus_dm = pd.Series(0.0, index=high_ser.index)
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
    
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    dx = dx.fillna(0)
    adx_value = dx.ewm(alpha=1/period, adjust=False).mean().iloc[-1]
    return adx_value

def supertrend(symbol, period, interval, multiplier=3):
    """
    Calculate the Supertrend indicator.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: ATR period.
    :param interval: Interval for the candle data (e.g., "1d").
    :param multiplier: Multiplier for the ATR (default: 3).
    :return: Supertrend value.
    """
    candles = candle_list(symbol, period * 2, interval, field="all")
    if not candles:
        return None
        
    high_ser = pd.Series([c["high"] for c in candles])
    low_ser = pd.Series([c["low"] for c in candles])
    close_ser = pd.Series([c["close"] for c in candles])
    
    tr1 = high_ser - low_ser
    tr2 = (high_ser - close_ser.shift(1)).abs()
    tr3 = (low_ser - close_ser.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    hl2 = (high_ser + low_ser) / 2
    basic_upperband = hl2 + multiplier * atr
    basic_lowerband = hl2 - multiplier * atr
    
    final_upperband = pd.Series(0.0, index=high_ser.index)
    final_lowerband = pd.Series(0.0, index=high_ser.index)
    supertrend_vals = pd.Series(0.0, index=high_ser.index)
    
    for i in range(1, len(high_ser)):
        if pd.isna(atr[i]): continue
        
        # Final Upper Band
        if basic_upperband[i] < final_upperband[i-1] or close_ser[i-1] > final_upperband[i-1]:
            final_upperband[i] = basic_upperband[i]
        else:
            final_upperband[i] = final_upperband[i-1]
            
        # Final Lower Band
        if basic_lowerband[i] > final_lowerband[i-1] or close_ser[i-1] < final_lowerband[i-1]:
            final_lowerband[i] = basic_lowerband[i]
        else:
            final_lowerband[i] = final_lowerband[i-1]
            
        # Supertrend
        if supertrend_vals[i-1] == final_upperband[i-1] and close_ser[i] <= final_upperband[i]:
            supertrend_vals[i] = final_upperband[i]
        elif supertrend_vals[i-1] == final_upperband[i-1] and close_ser[i] > final_upperband[i]:
            supertrend_vals[i] = final_lowerband[i]
        elif supertrend_vals[i-1] == final_lowerband[i-1] and close_ser[i] >= final_lowerband[i]:
            supertrend_vals[i] = final_lowerband[i]
        elif supertrend_vals[i-1] == final_lowerband[i-1] and close_ser[i] < final_lowerband[i]:
            supertrend_vals[i] = final_upperband[i]
        else:
            supertrend_vals[i] = final_upperband[i]
            
    return supertrend_vals.iloc[-1]
