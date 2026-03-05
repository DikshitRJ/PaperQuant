from Candle_fetcher import candle_list
import pandas as pd

# Signal indicators generate binary or event-based outputs for strategies.
# Examples include Moving Average Crossovers, RSI Divergence, Breakout Detection, etc.

def moving_average_crossover(symbol, period, interval, short_period=9, long_period=21):
    """
    Detect Moving Average Crossover.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Number of candles to fetch (should be at least long_period + 1).
    :param interval: Interval for the candle data (e.g., "1d").
    :param short_period: Short moving average period.
    :param long_period: Long moving average period.
    :return: Signal (1 for bullish crossover, -1 for bearish crossover, 0 for no signal).
    """
    prices = candle_list(symbol, period, interval, field="close")
    if not prices or len(prices) < long_period + 1:
        return 0
        
    prices_ser = pd.Series(prices)
    short_ma = prices_ser.rolling(window=short_period).mean()
    long_ma = prices_ser.rolling(window=long_period).mean()
    
    if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
        return 1  # Bullish crossover
    elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
        return -1  # Bearish crossover
    return 0

def breakout_detection(symbol, period, interval):
    """
    Detect breakout above rolling high or below rolling low.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size for high/low.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Signal (1 for breakout above high, -1 for breakout below low, 0 for no breakout).
    """
    prices = candle_list(symbol, period + 1, interval, field="close")
    if not prices or len(prices) < period + 1:
        return 0
        
    prices_ser = pd.Series(prices)
    # Use previous 'period' candles to find resistance/support
    resistance = prices_ser.iloc[:-1].rolling(window=period).max().iloc[-1]
    support = prices_ser.iloc[:-1].rolling(window=period).min().iloc[-1]
    
    current_price = prices_ser.iloc[-1]
    
    if current_price > resistance:
        return 1  # Breakout above resistance
    elif current_price < support:
        return -1  # Breakout below support
    return 0
