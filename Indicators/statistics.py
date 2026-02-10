from Candle_fetcher import candle_list

import pandas as pd

# Statistical indicators are useful for quant-style strategies and filtering.
# Examples include Z-score, Linear Regression, Rolling Sharpe Ratio, etc.

def z_score(prices, window):
    """
    Calculate the Z-score of prices over a rolling window.
    :param prices: List of prices.
    :param window: Rolling window size.
    :return: Z-score value.
    """
    rolling_mean = pd.Series(prices).rolling(window=window).mean()
    rolling_std = pd.Series(prices).rolling(window=window).std()
    z_score = (prices[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]
    return z_score

def rolling_sharpe_ratio(returns, window):
    """
    Calculate the rolling Sharpe Ratio.
    :param returns: List of returns.
    :param window: Rolling window size.
    :return: Rolling Sharpe Ratio value.
    """
    rolling_mean = pd.Series(returns).rolling(window=window).mean()
    rolling_std = pd.Series(returns).rolling(window=window).std()
    sharpe_ratio = rolling_mean.iloc[-1] / rolling_std.iloc[-1]
    return sharpe_ratio