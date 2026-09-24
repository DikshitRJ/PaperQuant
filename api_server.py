from __future__ import annotations

import os
import socket

import uvicorn

from api.app import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    port = find_free_port()
    port_file = os.path.expanduser("~/.paperquant/port")
    os.makedirs(os.path.dirname(port_file), exist_ok=True)
    with open(port_file, "w", encoding="utf-8") as handle:
        handle.write(str(port))
    print(f"PAPERQUANT_PORT={port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    import runpy
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "run-trade-adapter":
            import Trade_adapter
            Trade_adapter.main()
            sys.exit(0)
        elif cmd == "run-price-adapter":
            import asyncio

            from Price_adapter import main as price_main
            asyncio.run(price_main.main())
            sys.exit(0)
        elif cmd == "run-strategy":
            if len(sys.argv) > 2:
                script_path = sys.argv[2]
                runpy.run_path(script_path, run_name="__main__")
            sys.exit(0)
            
    main()
