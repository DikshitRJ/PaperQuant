import json
import asyncio
from fetch import fetch_multiple_candles
from db_handler import imt_mongo, update_redis_candles
from live_fetch import main as live_fetch_main


async def periodic_fetch_and_store(stocklist: list[str]):
    # Convert once, do NOT mutate later
    #stocklist_str = " ".join(stocklist)

    while True:
        try:
            # Fetch updated ticker prices
            updated_prices = fetch_multiple_candles(stocklist, interval='1m', lookback_minutes=3)

            # Write to MongoDB
            imt_mongo(list(updated_prices.values()))
            for ticker, candle_data in updated_prices.items():
                candle_data = dict(candle_data)      # shallow copy
                candle_data.pop("_id", None)          # remove Mongo artifact
                update_redis_candles(ticker, candle_data)

        except Exception as e:
            print(f"Error during periodic fetch and store: {e}")

        await asyncio.sleep(60)


async def main():
    # Load stocklist safely
    with open("stocklist.json", "r") as f:
        stocklist: list[str] = json.load(f)

    # Defensive check (optional but recommended)
    assert isinstance(stocklist, list)
    assert all(isinstance(x, str) for x in stocklist)

    # Pass independent copies to concurrent tasks
    asyncio.create_task(live_fetch_main(stocklist.copy()))
    await periodic_fetch_and_store(stocklist.copy())


if __name__ == "__main__":
    asyncio.run(main())
