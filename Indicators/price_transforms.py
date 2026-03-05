from Candle_fetcher import candle_list
import pandas as pd

# Price transformation utilities preprocess price data for use in indicators.
# Examples include Typical Price, Median Price, Weighted Close, etc.

def typical_price(symbol, period, interval):
    """
    Calculate the Typical Price.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Typical Price value.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high = candles[-1]["high"]
    low = candles[-1]["low"]
    close = candles[-1]["close"]
    return (high + low + close) / 3

def median_price(symbol, period, interval):
    """
    Calculate the Median Price.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Period for calculation.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Median Price value.
    """
    candles = candle_list(symbol, period, interval, field="all")
    if not candles:
        return None
        
    high = candles[-1]["high"]
    low = candles[-1]["low"]
    return (high + low) / 2
