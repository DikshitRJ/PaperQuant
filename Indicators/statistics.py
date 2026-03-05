from Candle_fetcher import candle_list
import pandas as pd

# Statistical indicators are useful for quant-style strategies and filtering.
# Examples include Z-score, Linear Regression, Rolling Sharpe Ratio, etc.

def z_score(symbol, period, interval):
    """
    Calculate the Z-score of prices over a rolling window.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Z-score value.
    """
    prices = candle_list(symbol, period, interval, field="close")
    if not prices:
        return None
        
    prices_ser = pd.Series(prices)
    rolling_mean = prices_ser.rolling(window=period).mean()
    rolling_std = prices_ser.rolling(window=period).std()
    z_score_val = (prices_ser.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]
    return z_score_val

def rolling_sharpe_ratio(symbol, period, interval):
    """
    Calculate the rolling Sharpe Ratio.
    :param symbol: Stock symbol (e.g., "AAPL").
    :param period: Rolling window size.
    :param interval: Interval for the candle data (e.g., "1d").
    :return: Rolling Sharpe Ratio value.
    """
    prices = candle_list(symbol, period + 1, interval, field="close")
    if not prices:
        return None
        
    returns = pd.Series(prices).pct_change().dropna()
    rolling_mean = returns.rolling(window=period).mean()
    rolling_std = returns.rolling(window=period).std()
    sharpe_ratio = rolling_mean.iloc[-1] / rolling_std.iloc[-1]
    return sharpe_ratio
