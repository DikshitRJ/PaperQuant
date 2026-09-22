#!/bin/bash

# Reads dynamic port if available
PORT=$(cat ~/.paperquant/port 2>/dev/null || echo 8000)

curl -X POST http://127.0.0.1:$PORT/api/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "watchlist": [
      { "ticker": "AAPL", "capital": 1000.0 },
      { "ticker": "MSFT", "capital": 2000.0 }
    ],
    "strategy_id": "my_rsi_strategy",
    "settings": {
      "simulated_latency_ms": 0,
      "commission_percent": 0.0,
      "leverage": 1
    }
  }'
