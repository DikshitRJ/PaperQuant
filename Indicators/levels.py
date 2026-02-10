from Candle_fetcher import candle_list

import pandas as pd

# Support and resistance indicators calculate key price levels.
# Examples include Pivot Points, Fibonacci Retracements, Rolling High/Low, etc.

def pivot_points(high, low, close):
    """
    Calculate Pivot Points (Classic formula).
    :param high: List of high prices.
    :param low: List of low prices.
    :param close: List of close prices.
    :return: Dictionary with pivot point, support, and resistance levels.
    """
    pivot = (high + low + close) / 3
    support1 = (2 * pivot) - high
    resistance1 = (2 * pivot) - low
    return {"pivot": pivot, "support1": support1, "resistance1": resistance1}

def rolling_high_low(prices, window):
    """
    Calculate rolling high and low over a specified window.
    :param prices: List of prices.
    :param window: Rolling window size.
    :return: Tuple of rolling high and rolling low.
    """
    rolling_high = pd.Series(prices).rolling(window=window).max()
    rolling_low = pd.Series(prices).rolling(window=window).min()
    return rolling_high.iloc[-1], rolling_low.iloc[-1]