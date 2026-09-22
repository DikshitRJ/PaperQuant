# Trade_adapter.py

This file acts as the Advanced Trade Adapter for the PaperQuant system. It listens for simulated trade orders via ZeroMQ and processes them against cached state and live prices.

## Core Responsibilities
- **ZeroMQ ROUTER**: Listens for incoming buy/sell requests on `SIM_TRADE_BIND_ENDPOINT`.
- **State & Live Price Cache**: Uses `diskcache` to store current positions (`qty`, `avg_price`), capital per symbol, and retrieves delayed live prices to simulate real market conditions.
- **Order Execution Logic**: 
  - Validates market orders vs limit orders.
  - Pends limit orders if the target price is not yet met.
  - Applies simulated latency and commission percentages based on user settings.
  - Properly calculates weighted average prices for increasing positions, and handles position flipping (e.g., short to long).
- **Position Management (Recent Updates)**:
  - Specifically handles `update_position` for correct long and short tracking.
  - Implements persistent pending orders logic so limits are checked continuously in the main loop until executed or cancelled.
- **Logging**: Persists every executed trade to `order_history.csv`.
