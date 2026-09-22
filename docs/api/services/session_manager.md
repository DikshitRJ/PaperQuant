# session_manager.py

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
