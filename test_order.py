import asyncio
import os
import sys

# Add root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock environment
os.environ["SIM_STRATEGY_ID"] = "test_strat"
os.environ["SIM_SYMBOL"] = "AAPL"
os.environ["SIM_TRADE_ENDPOINT"] = "tcp://127.0.0.1:5555"

from Handler import action


async def run_test():
    print("Sending Buy Order for 10 AAPL...")
    response = await action.buy(10)
    print(f"Response: {response}")

    if response.get("status") == "ok":
        print("Order Successful!")
    else:
        print("Order Failed!")


if __name__ == "__main__":
    asyncio.run(run_test())
