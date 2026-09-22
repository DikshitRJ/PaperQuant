import asyncio
import json
import os

import websockets


async def listen_to_paperquant():
    # Read dynamic port
    port_file = os.path.expanduser("~/.paperquant/port")
    port = 8000
    if os.path.exists(port_file):
        with open(port_file, "r") as f:
            port = int(f.read().strip())

    uri = f"ws://127.0.0.1:{port}/ws"

    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Listening for events...")
            while True:
                message = await websocket.recv()
                event = json.loads(message)
                print(f"[{event['timestamp']}] {event['type']}:")
                print(json.dumps(event["data"], indent=2))
    except ConnectionRefusedError:
        print("Could not connect. Is the PaperQuant API server running?")


if __name__ == "__main__":
    asyncio.run(listen_to_paperquant())
