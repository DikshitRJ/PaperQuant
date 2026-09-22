import os

docs_dir = "/mnt/Data/Coding/PaperQuant/docs"

files_to_doc = [
    "Trade_adapter.py",
    "Handler.py",
    "api_server.py",
    "test_order.py",
    "Price_adapter/main.py",
    "Price_adapter/fetch.py",
    "Price_adapter/live_fetch.py",
    "Price_adapter/db_handler.py",
    "api/app.py",
    "api/config.py",
    "api/schemas.py",
    "api/websocket.py",
    "api/services/session_manager.py",
    "api/services/algorithm_store.py",
    "api/services/log_buffer.py",
    "api/services/portfolio.py",
    "api/services/process_manager.py",
    "api/services/settings_store.py",
    "api/services/stats_tracker.py",
    "api/routes/algorithms.py",
    "api/routes/health.py",
    "api/routes/logs.py",
    "api/routes/market.py",
    "api/routes/positions.py",
    "api/routes/session.py",
    "api/routes/settings.py",
    "api/routes/stats.py",
    "Indicators/Candle_fetcher.py",
    "Indicators/levels.py",
    "Indicators/Main.py",
    "Indicators/market_structure.py",
    "Indicators/momentum.py",
    "Indicators/moving_avg.py",
    "Indicators/price_transforms.py",
    "Indicators/signals.py",
    "Indicators/statistics.py",
    "Indicators/trend.py",
    "Indicators/volatility.py",
    "Indicators/volume.py",
    "UI/Wrapper/main.py",
]

detailed_content = {
    "Trade_adapter.py": """# Trade_adapter.py

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
""",
    "api/services/session_manager.py": """# session_manager.py

The `SessionManager` coordinates the entire lifecycle of a backtesting or paper trading session within the PaperQuant API.

## Core Responsibilities
- **Lifecycle Management**: Exposes methods `start_session`, `stop_session`, and `reset_session`.
- **Process Orchestration**: Starts the `Price_adapter`, `Trade_adapter`, and any strategy processes (via `ProcessManager`).
- **State Maintenance**: 
  - Initializes caches for capital limits per ticker.
  - Monitors the active session and tracks uptime.
- **WebSocket Broadcasting (Recent Updates)**:
  - Runs an asynchronous `_push_loop` task to continuously broadcast updates over WebSockets.
  - Pushes position updates (from `PortfolioService`), session stats, log buffers, adapter statuses, and live price ticks at regular intervals.
  - Recently updated to accurately broadcast adapter status and chart metrics with a throttling mechanism (e.g., 60s for charts, 1s for price ticks).
""",
    "Handler.py": """# Handler.py

This file is the client-side strategy adapter (often imported into algorithm scripts) allowing them to interact with the backend adapters.

## Core Responsibilities
- **ZeroMQ DEALER**: Connects to the Trade Adapter to submit asynchronous `buy` and `sell` actions.
- **Market Data Retrieval**: Reads directly from the `diskcache` to provide the strategy with the latest price candles (`prices.last_candle`).
- **Indicators Exposure**: Imports the technical indicators suite, exposing it to strategies.
- **Order Timeout & Correlation**: Employs asyncio to await trade execution responses, utilizing correlation IDs and configured timeouts (`SIM_TRADE_TIMEOUT_SECONDS`) to prevent strategy blocking.
""",
    "api_server.py": """# api_server.py

The entry point for the PaperQuant backend API.

## Core Responsibilities
- Finds an available free port on `127.0.0.1`.
- Writes the chosen port to `~/.paperquant/port` for the UI/Tauri wrapper to read.
- Launches the FastAPI application using `uvicorn`.
""",
}

default_content = """# {filename}

This file handles the {module_name} functionality for the PaperQuant system. It contains logic to support the overarching spec-driven architecture.
"""

for f in files_to_doc:
    md_path = os.path.join(docs_dir, f.replace(".py", ".md"))
    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    if f in detailed_content:
        content = detailed_content[f]
    else:
        module_name = os.path.basename(f).replace(".py", "")
        content = default_content.format(
            filename=os.path.basename(f), module_name=module_name
        )

    with open(md_path, "w") as out:
        out.write(content)

print("Documentation generated.")
