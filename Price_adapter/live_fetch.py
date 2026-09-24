import asyncio
import os
import time

import yfinance as yf
from diskcache import Cache


def init_cache():
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.config import LIVE_PRICES_CACHE_PATH
    return Cache(str(LIVE_PRICES_CACHE_PATH), timeout=30)


import random


async def mock_generator(cache, stocklist):
    """Generates random price movements if the market is closed."""
    # Seed initial prices
    prices = {s: 150.0 + random.uniform(-50, 50) for s in stocklist}
    while True:
        for stock in stocklist:
            prices[stock] += random.uniform(-0.5, 0.5)
            cache_key = f"prices:{stock}"
            current_data = cache.get(cache_key, [])
            if not isinstance(current_data, list):
                current_data = []

            now = time.time()  # Use wall clock to match Trade_adapter
            current_data.append({"price": round(prices[stock], 2), "ts": now})
            cutoff = now - 120
            current_data = [d for d in current_data if d["ts"] > cutoff]
            cache.set(cache_key, current_data)
        await asyncio.sleep(1)


async def main(stocklist):
    cache = init_cache()
    mock_task = None

    async def handle(message):
        # If we get real data, we could potentially stop/pause the mock,
        # but for simplicity, real data will just coexist or overwrite.
        stock = message["id"]
        price = message["price"]
        cache_key = f"prices:{stock}"
        current_data = cache.get(cache_key, [])
        if not isinstance(current_data, list):
            current_data = []
        now = time.time()
        current_data.append({"price": price, "ts": now})
        cutoff = now - 120
        current_data = [d for d in current_data if d["ts"] > cutoff]
        cache.set(cache_key, current_data)

    try:
        async with yf.AsyncWebSocket(verbose=False) as ws:
            await ws.subscribe(stocklist)
            print("Subscribed to symbols:", stocklist)
            while True:
                await ws.listen(handle)
    except Exception as e:
        print(f"WebSocket unavailable (likely market closed): {e}")
        mock_task = asyncio.create_task(mock_generator(cache, stocklist))
        await mock_task
    finally:
        if mock_task is not None:
            mock_task.cancel()
        cache.close()


if __name__ == "__main__":
    stocklist = ["AAPL", "GOOG", "MSFT"]
    try:
        asyncio.run(main(stocklist))
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Exiting.")
        os._exit(0)
