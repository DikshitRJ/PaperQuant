import yfinance as yf
import redis.asyncio as redis

async def main(stocklist):
    redis_client = redis.from_url("redis://localhost", db=1)

    async with yf.AsyncWebSocket() as ws:
        await ws.subscribe(stocklist)
        print("Subscribed to symbols:", stocklist)

        while True:
            message = await ws.listen()   # ← THIS is the correct call

            if message is None:
                continue

            stock = message["symbol"]
            price = message["price"]

            await redis_client.lpush(f"prices:{stock}", price)
            await redis_client.ltrim(f"prices:{stock}", 0, 9)
