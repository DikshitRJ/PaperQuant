# main.py

This file is the entry point for the Price Adapter in the PaperQuant system.

## Core Responsibilities
- **Continuous Market Data Fetching**: Reads `stocklist.json` and runs an asyncio loop to fetch 1-minute interval candles every 60 seconds.
- **Data Persistence**: Uses `fetch_multiple_candles` to get prices, stores them in SQLite via `imt_sqlite`, and updates the shared disk cache via `update_diskcache_candles`.
- **Live Price Streams**: Spawns a background task `live_fetch_main` to continuously poll and broadcast sub-minute live prices.
