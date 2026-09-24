import asyncio
import json

from db_handler import imt_sqlite, update_diskcache_candles
from fetch import fetch_multiple_candles
from live_fetch import main as live_fetch_main


async def periodic_fetch_and_store(stocklist: list[str]):
    # stocklist_str = " ".join(stocklist)

    while True:
        try:
            updated_prices = await asyncio.to_thread(
                fetch_multiple_candles,
                stocklist,
                interval="1m",
                lookback_minutes=3,
            )

            imt_sqlite(list(updated_prices.values()))
            for ticker, candle_data in updated_prices.items():
                candle_data = dict(candle_data)  # shallow copy
                update_diskcache_candles(ticker, candle_data)

        except Exception as e:
            print(f"Error during periodic fetch and store: {e}")

        await asyncio.sleep(60)


async def main():
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.config import TEMP_DIR

    stocklist_path = TEMP_DIR / "stocklist.json"
    with open(stocklist_path, "r") as f:
        stocklist: list[str] = json.load(f)
    live_task = asyncio.create_task(live_fetch_main(stocklist.copy()))

    try:
        await periodic_fetch_and_store(stocklist.copy())
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("Main loop interrupted.")
    finally:
        print("Cancelling live fetch task...")
        live_task.cancel()
        try:
            await live_task
        except asyncio.CancelledError:
            print("Live fetch task successfully killed.")


if __name__ == "__main__":
    asyncio.run(main())
