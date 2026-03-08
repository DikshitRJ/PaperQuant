# Import all modules in the Indicators directory using relative imports
from . import levels
from . import market_structure
from . import moving_avg
from . import momentum
from . import volume
from . import volatility
from . import trend
from . import statistics
from . import signals
from . import price_transforms

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