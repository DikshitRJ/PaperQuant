from candle_fetcher import candle_list

import pandas as pd

# Price transformation utilities preprocess price data for use in indicators.
# Examples include Typical Price, Median Price, Weighted Close, etc.

def typical_price(high, low, close):
    """
    Calculate the Typical Price.
    :param high: List of high prices.
    :param low: List of low prices.
    :param close: List of close prices.
    :return: Typical Price value.
    """
    return (high + low + close) / 3

def median_price(high, low):
    """
    Calculate the Median Price.
    :param high: List of high prices.
    :param low: List of low prices.
    :return: Median Price value.
    """
    return (high + low) / 2