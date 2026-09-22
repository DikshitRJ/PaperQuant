# Handler.py

This file is the client-side strategy adapter (often imported into algorithm scripts) allowing them to interact with the backend adapters.

## Core Responsibilities
- **ZeroMQ DEALER**: Connects to the Trade Adapter to submit asynchronous `buy` and `sell` actions.
- **Market Data Retrieval**: Reads directly from the `diskcache` to provide the strategy with the latest price candles (`prices.last_candle`).
- **Indicators Exposure**: Imports the technical indicators suite, exposing it to strategies.
- **Order Timeout & Correlation**: Employs asyncio to await trade execution responses, utilizing correlation IDs and configured timeouts (`SIM_TRADE_TIMEOUT_SECONDS`) to prevent strategy blocking.
