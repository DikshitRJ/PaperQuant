from Candle_fetcher import candle_list

import pandas as pd

# Signal indicators generate binary or event-based outputs for strategies.
# Examples include Moving Average Crossovers, RSI Divergence, Breakout Detection, etc.

def moving_average_crossover(short_ma, long_ma):
    """
    Detect Moving Average Crossover.
    :param short_ma: List of short moving average values.
    :param long_ma: List of long moving average values.
    :return: Signal (1 for bullish crossover, -1 for bearish crossover, 0 for no signal).
    """
    if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
        return 1  # Bullish crossover
    elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
        return -1  # Bearish crossover
    return 0

def breakout_detection(prices, resistance, support):
    """
    Detect breakout above resistance or below support levels.
    :param prices: List of prices.
    :param resistance: Resistance level.
    :param support: Support level.
    :return: Signal (1 for breakout above resistance, -1 for breakout below support, 0 for no breakout).
    """
    if prices[-1] > resistance:
        return 1  # Breakout above resistance
    elif prices[-1] < support:
        return -1  # Breakout below support
    return 0