import yfinance as yf
from diskcache import Cache

def init_cache():
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

            prices = cache.get(cache_key, [])

            prices.insert(0, price)
            
            prices = prices[:10]

            cache.set(cache_key, prices)
