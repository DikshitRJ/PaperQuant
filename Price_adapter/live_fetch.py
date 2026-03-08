import yfinance as yf
from diskcache import Cache
import asyncio
import os
def init_cache():
    return Cache("./Temporary/cache_liveprices", timeout=30)


async def main(stocklist):
    cache = init_cache()
    async def handle(message):
        stock = message["id"]
        price = message["price"]
        print("stock:", stock, "\n price:", price)
        cache_key = f"prices:{stock}"
        
        # Store multiple responses to allow delayed price pulling
        current_data = cache.get(cache_key, [])
        if not isinstance(current_data, list):
            current_data = []
            
        now = asyncio.get_event_loop().time()
        current_data.append({"price": price, "ts": now})
        
        # Retain only the last 1.5 minutes (90 seconds)
        cutoff = now - 90
        current_data = [d for d in current_data if d["ts"] > cutoff]
        
        cache.set(cache_key, current_data)
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
