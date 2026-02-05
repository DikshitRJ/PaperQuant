import yfinance as yf
from diskcache import Cache
import asyncio
import os
def init_cache():
    return Cache("./Temporary/cache_liveprices")


async def main(stocklist):
    cache = init_cache()
    async def handle(message):
        stock = message["id"]
        price = message["price"]
        print("stock:", stock, "\n price:", price)
        cache_key = f"prices:{stock}"
        prices = cache.get(cache_key, [])
        prices.insert(0, price)
        cache.set(cache_key, prices[:10])
        #cache.flush()

    try:
        async with yf.AsyncWebSocket(verbose=False) as ws:
            await ws.subscribe(stocklist)
            print("Subscribed to symbols:", stocklist)

            while True:
                message = await ws.listen(handle)
                if not message:
                    continue
    except asyncio.CancelledError:
        print("Shutting down gracefully...")
        raise
    finally:
        cache.close()
        print("Cache closed. Program exited.")

if __name__ == "__main__":
    stocklist = ["AAPL", "GOOG", "MSFT"]
    try:
        asyncio.run(main(stocklist))
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Exiting.")
        os._exit(0)
