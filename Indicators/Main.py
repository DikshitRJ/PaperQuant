# Import all modules in the Indicators directory
import levels
import market_structure
import moving_avg
import momentum
import volume
import volatility
import trend
import statistics
import signals
import price_transforms

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