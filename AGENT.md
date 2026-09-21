# PaperQuant Agent Documentation

## Project Overview
**PaperQuant** is an interactive, open-source paper trading platform designed for algorithmic traders. It provides a modular environment to develop, test, and execute trading strategies in a simulated environment using real-time market data.

The system is built on a decoupled architecture where data fetching, trade execution, and strategy logic are separated, communicating via **ZeroMQ (ZMQ)** and shared **DiskCache**.

---

## Directory Structure & File Breakdown

### Root Directory
- **Handler.py**: The primary API for strategy developers. It provides the `indicators` and `action` namespaces. It acts as a ZMQ **DEALER**, sending trade requests to the Trade Adapter and receiving execution confirmations.
- **Trade_adapter.py**: The execution engine. It acts as a ZMQ **ROUTER**, managing positions, logging trades to CSV, and maintaining the account state in `Temporary/state`.
- **pyproject.toml**: Defines project metadata and dependencies (e.g., `yfinance`, `diskcache`, `pyzmq`, `pandas`).
- **poetry.lock**: Lockfile for Python dependencies.
- **LICENSE**: GPL-3.0-or-later license.
- **README.md**: Project introduction (currently empty/placeholder).

### [Indicators/](./Indicators)
A modular library of technical analysis tools.
- **Main.py**: The entry point that aggregates all indicator modules into a single `indicators` class.
- **Candle_fetcher.py**: Handles fetching historical candle data via `yfinance` for indicator calculations.
- **levels.py**: Support/Resistance and price level detection.
- **market_structure.py**: Trend shifts, breaks of structure (BOS), and change of character (CHoCH).
- **momentum.py**: Oscillators like RSI, MACD, and other momentum metrics.
- **moving_avg.py**: EMA, SMA, and other moving average variants.
- **price_transforms.py**: Log transforms and basic price manipulations.
- **signals.py**: Logic for generating specific buy/sell signals.
- **statistics.py**: Mathematical tools like standard deviation, variance, and correlation.
- **trend.py**: Trend direction and strength indicators (e.g., ADX).
- **volatility.py**: ATR, Bollinger Bands, and volatility measurement.
- **volume.py**: Volume-weighted indicators (VWAP, OBV).

### [Price_adapter/](./Price_adapter)
Manages the inflow of market data.
- **main.py**: Orchestrates periodic fetching of OHLCV data.
- **fetch.py**: Logic for batch-fetching candles.
- **live_fetch.py**: Handles high-frequency live price updates.
- **db_handler.py**: Manages data persistence, saving candles to **SQLite** (`paperquant.db`) and real-time updates to **DiskCache**.

### [UI/](./UI)
The visualization and control layer.
- **Frontend/**: A modern **React + TypeScript** application built with **Vite** and **Tailwind CSS**.
  - **components/**: UI elements like `PositionsTable`, `ExecutionTerminal`, and `StatCard`.
  - **hooks/useBackend.ts**: Integration hook designed to communicate with a Python backend via `pywebview`.
- **Wrapper/**: Intended for the Python script that wraps the React frontend into a desktop application.

### [Temporary/](./Temporary)
Storage for runtime data.
- **cache_candles/**: DiskCache directory for OHLCV data.
- **cache_liveprices/**: DiskCache directory for real-time price ticks.
- **state/**: DiskCache directory for trading positions and account balance.
- **paperquant.db**: SQLite database for historical data persistence.
- **order_history.csv**: A human-readable log of all executed trades.

---

## Core System Workflow

1.  **Data Ingestion**: `Price_adapter` fetches data from `yfinance`. It stores historical data in SQLite and "Live" data in `DiskCache`.
2.  **Strategy Execution**: A strategy (using `Handler.py`) reads indicators from the `Indicators` module.
3.  **Analysis**: The `indicators` fetch needed data through `Candle_fetcher.py`.
4.  **Trading**: When a strategy decides to trade, it calls `action.buy()` or `action.sell()`. `Handler.py` sends a JSON payload via ZMQ to the `Trade_adapter.py`.
5.  **Execution**: `Trade_adapter.py` verifies the price, updates the virtual portfolio in `Temporary/state`, and logs the trade.
6.  **Monitoring**: The `UI` (React) displays real-time positions and logs by communicating with the underlying Python processes.

---

## Technical Stack
- **Language**: Python 3.10+
- **Communication**: ZeroMQ (ZMQ) for Inter-Process Communication (IPC).
- **Caching**: DiskCache for low-latency shared state.
- **Database**: SQLite for persistent storage.
- **Data Source**: Yahoo Finance (`yfinance`).
- **Frontend**: React, TypeScript, Vite, Tailwind CSS.
- **Integration**: Designed for `pywebview` desktop encapsulation.
