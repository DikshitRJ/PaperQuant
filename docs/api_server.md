# api_server.py

The entry point for the PaperQuant backend API.

## Core Responsibilities
- Finds an available free port on `127.0.0.1`.
- Writes the chosen port to `~/.paperquant/port` for the UI/Tauri wrapper to read.
- Launches the FastAPI application using `uvicorn`.
