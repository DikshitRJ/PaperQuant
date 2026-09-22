# Import all modules in the Indicators directory using relative imports
from . import (
    levels,
    market_structure,
    momentum,
    moving_avg,
    price_transforms,
    signals,
    statistics,
    trend,
    volatility,
    volume,
)


# Create a unified namespace for all indicators
class indicators:
    levels = levels
    market_structure = market_structure
    moving_avg = moving_avg
    momentum = momentum
    volume = volume
    volatility = volatility
    trend = trend
    statistics = statistics
    signals = signals
    price_transforms = price_transforms
