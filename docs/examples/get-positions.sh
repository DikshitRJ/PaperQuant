#!/bin/bash

# Reads dynamic port if available
PORT=$(cat ~/.paperquant/port 2>/dev/null || echo 8000)

curl -X GET http://127.0.0.1:$PORT/api/positions
