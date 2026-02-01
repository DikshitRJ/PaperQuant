import yfinance as yf
from diskcache import Cache

def init_cache():
    # Directory is created automatically if it doesn't exist
    return Cache("./Temporary/cache_liveprices")

async def main(stocklist):
    cache = init_cache()

    async with yf.AsyncWebSocket() as ws:
        await ws.subscribe(stocklist)
        print("Subscribed to symbols:", stocklist)

        while True:
            message = await ws.listen()

            if message is None:
                continue

            stock = message["symbol"]
            price = message["price"]

            cache_key = f"prices:{stock}"

            # Get existing price list (newest first)
            prices = cache.get(cache_key, [])

            # LPUSH equivalent
            prices.insert(0, price)

            # LTRIM 0 9 equivalent
            prices = prices[:10]

            cache.set(cache_key, prices)
