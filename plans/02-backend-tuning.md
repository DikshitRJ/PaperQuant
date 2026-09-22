# Plan 2: Backend Tuning & Adjustment

> **Phase**: 2 of 4 (Runs in PARALLEL with Plan 3 after Plan 1 is finalized)  
> **Depends on**: Plan 1 (API Specification) — the single source of truth  
> **Estimated Effort**: ~12 hours  
> **Output**: A fully functional FastAPI backend server that implements every endpoint from the API spec

---

## 1. Goal

Replace the `pywebview` `API` class with a FastAPI HTTP/WebSocket server that:
- Implements every endpoint defined in `plans/01-api-specification.md`
- Fixes all known bugs in the existing backend code
- Adds missing features (algorithm management, strategy execution, P&L computation, settings persistence)
- Preserves the existing ZMQ/DiskCache/SQLite multi-process architecture
- Is packageable as a standalone PyInstaller binary for Tauri sidecar

---

## 2. Current State & Bug Inventory

### 2.1 Critical Bugs to Fix

| Bug | Location | Fix |
|---|---|---|
| **Position data schema mismatch** | `UI/Wrapper/main.py` L179 | Backend sends `{strategy_id, symbol, qty, avg_price}` but frontend needs `{ticker, initials, pnl, invested, current}`. New API must compute and format all fields. |
| **Log data schema mismatch** | `UI/Wrapper/main.py` L133 | Backend sends `{id, message, timestamp, type}` but frontend needs `{time, content, color}`. New API must format logs correctly. |
| **`live_fetch.py` import ordering** | `Price_adapter/live_fetch.py` L22 vs L29 | Move `import time` to top of file |
| **Mock + real WS collision** | `Price_adapter/live_fetch.py` L35 | Only spawn mock if WebSocket connection fails |
| **Price_adapter CWD bug** | `UI/Wrapper/main.py` L194 | Launch with `cwd=Price_adapter/` or convert to package imports |
| **`trend.py` missing numpy import** | `Indicators/trend.py` L41 | Add `import numpy as np` at top |
| **Platform-specific Python path** | `UI/Wrapper/main.py` L18 | Use `sys.executable` instead of hardcoded `.venv/bin/python` |
| **`requires-python` too strict** | `pyproject.toml` | Change to `>=3.10,<4.0` |
| **Missing dependencies** | `pyproject.toml` | Add `pandas`, `numpy`, `fastapi`, `uvicorn`, `websockets` |
| **Blocking yfinance in asyncio** | `Price_adapter/main.py` L13 | Wrap in `asyncio.to_thread()` |
| **Indefinite deadlock on limit orders** | `Handler.py` L73 | Add correlation IDs and timeout |
| **Pending orders lost on restart** | `Trade_adapter.py` L182 | Persist to DiskCache |

### 2.2 Missing Features to Implement

| Feature | Priority | Details |
|---|---|---|
| **FastAPI server** | P0 | Replace pywebview API class with HTTP+WS server |
| **Session management** | P0 | Start/stop/reset session via HTTP endpoints |
| **Position enrichment** | P0 | Compute P&L, format currency strings, add initials |
| **Algorithm management** | P0 | Upload, register, list, delete `.py` strategy scripts |
| **Strategy execution** | P0 | Spawn user strategy scripts as subprocesses |
| **Settings persistence** | P1 | Read/write settings to JSON config file |
| **P&L aggregation** | P1 | Compute session-level and global statistics |
| **P&L time series** | P1 | Track P&L snapshots for chart rendering |
| **Trade history** | P1 | Parse `order_history.csv` into JSON (later migrate to SQLite) |
| **Log formatting** | P1 | Format logs with time, content, color categories |
| **WebSocket event push** | P0 | Replace evaluate_js polling with async WS events |
| **Uptime tracking** | P2 | Session start time → compute elapsed time |
| **Commission/latency** | P2 | Apply simulated commission and latency from settings |
| **Capital enforcement** | P2 | Respect per-ticker capital limits from session config |

---

## 3. New File Structure

```
PaperQuant/
├── api_server.py              ← [NEW] FastAPI application entry point
├── api/
│   ├── __init__.py            ← [NEW]
│   ├── app.py                 ← [NEW] FastAPI app factory
│   ├── schemas.py             ← [NEW] Pydantic models (from API spec)
│   ├── routes/
│   │   ├── __init__.py        ← [NEW]
│   │   ├── health.py          ← [NEW] GET /api/health
│   │   ├── session.py         ← [NEW] POST /api/session/{start,stop,reset}, GET /api/session/status
│   │   ├── positions.py       ← [NEW] GET /api/positions, GET /api/positions/history
│   │   ├── stats.py           ← [NEW] GET /api/stats, GET /api/stats/chart
│   │   ├── algorithms.py      ← [NEW] CRUD /api/algorithms
│   │   ├── settings.py        ← [NEW] GET/PUT /api/settings
│   │   ├── logs.py            ← [NEW] GET /api/logs
│   │   └── market.py          ← [NEW] GET /api/market/prices
│   ├── websocket.py           ← [NEW] WebSocket /ws handler + event broadcaster
│   ├── services/
│   │   ├── __init__.py        ← [NEW]
│   │   ├── process_manager.py ← [NEW] Refactored from UI/Wrapper/main.py
│   │   ├── session_manager.py ← [NEW] Session lifecycle orchestration
│   │   ├── portfolio.py       ← [NEW] Position enrichment + P&L computation
│   │   ├── algorithm_store.py ← [NEW] Algorithm file management + metadata
│   │   ├── log_buffer.py      ← [NEW] Refactored LogBuffer with formatting
│   │   ├── settings_store.py  ← [NEW] Settings persistence
│   │   └── stats_tracker.py   ← [NEW] P&L time series tracking
│   └── config.py              ← [NEW] Paths, ports, defaults
├── algorithms/                ← [NEW] User algorithm storage directory
│   └── .gitkeep
├── Handler.py                 ← [MODIFY] Fix deadlock, add correlation IDs
├── Trade_adapter.py           ← [MODIFY] Fix pending orders persistence, add commission support
├── Price_adapter/
│   ├── main.py                ← [MODIFY] Fix blocking calls, convert to package imports
│   ├── fetch.py               ← [MODIFY] Minor cleanup
│   ├── live_fetch.py          ← [MODIFY] Fix import order, fix mock collision
│   └── db_handler.py          ← (no changes needed)
├── Indicators/
│   └── trend.py               ← [MODIFY] Add missing numpy import
├── pyproject.toml             ← [MODIFY] Add all missing dependencies
└── UI/Wrapper/main.py         ← [DEPRECATE] Replaced by api_server.py
```

---

## 4. Detailed Implementation Tasks

### 4.1 Task 1: Create FastAPI Application Skeleton

**File: `api/app.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import health, session, positions, stats, algorithms, settings, logs, market
from api.websocket import ws_router
from api.services.session_manager import SessionManager

session_manager = SessionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await session_manager.initialize()
    yield
    # Shutdown
    await session_manager.shutdown()

def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperQuant API",
        version="0.2.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost:*", "http://127.0.0.1:*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health.router, prefix="/api")
    app.include_router(session.router, prefix="/api")
    app.include_router(positions.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(algorithms.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")
    app.include_router(market.router, prefix="/api")
    app.include_router(ws_router)
    
    return app
```

**File: `api_server.py`** (entry point)

```python
import uvicorn
import socket
from api.app import create_app

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def main():
    port = find_free_port()
    
    # Write port to discoverable location for Tauri
    import os
    port_file = os.path.expanduser("~/.paperquant/port")
    os.makedirs(os.path.dirname(port_file), exist_ok=True)
    with open(port_file, 'w') as f:
        f.write(str(port))
    
    # Also print to stdout for Tauri to capture
    print(f"PAPERQUANT_PORT={port}", flush=True)
    
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
```

---

### 4.2 Task 2: Pydantic Schemas

**File: `api/schemas.py`**

Define all Pydantic models matching the API spec exactly:

```python
from pydantic import BaseModel
from typing import Optional, Literal

class WatchlistItem(BaseModel):
    ticker: str
    capital: float = 1000.0

class SessionStartRequest(BaseModel):
    watchlist: list[WatchlistItem]
    strategy_id: Optional[str] = None
    settings: Optional[dict] = None

class Position(BaseModel):
    ticker: str
    initials: str
    qty: int
    avg_price: float
    current_price: float
    invested: str
    current: str
    pnl: str
    pnl_percent: str
    strategy_id: str

class LogEntry(BaseModel):
    time: str
    content: str
    color: str

class Algorithm(BaseModel):
    id: str
    name: str
    filename: str
    dependencies: list[str]
    created_at: str
    history: list[dict] = []

class SessionStats(BaseModel):
    pnl: str
    invested: str
    current: str
    uptime: str
    trend: Literal['up', 'down', 'none']

class GlobalStats(BaseModel):
    total_pnl: str
    pnl_percent: str
    active_algos: str
    algo_runtime: str
    pnl_trend: Literal['up', 'down', 'none']

class Settings(BaseModel):
    currency: str = "USD"
    theme: str = "dark"
    simulated_latency_ms: int = 0
    commission_percent: float = 0.0
    leverage: int = 1
    auto_clear_logs: bool = True
    system_alerts: bool = True
    sound_effects: bool = False
    terminal_font_size: int = 14
```

---

### 4.3 Task 3: Refactor ProcessManager

**File: `api/services/process_manager.py`**

Refactor from `UI/Wrapper/main.py` with these changes:
- Use `sys.executable` instead of hardcoded `.venv/bin/python`
- Fix CWD for Price_adapter (set `cwd` to `Price_adapter/` directory)
- Add process health monitoring (check `poll()` for crashes)
- Add stdout/stderr capture to structured log buffer
- Support starting strategy subprocesses with proper env vars

```python
import sys
import os
import subprocess
import threading
from api.services.log_buffer import LogBuffer

class ProcessManager:
    def __init__(self, base_dir: str, log_buffer: LogBuffer):
        self.base_dir = base_dir
        self.log_buffer = log_buffer
        self.processes: dict[str, subprocess.Popen] = {}
    
    def start_process(self, name: str, cmd: list[str], cwd: str = None, env: dict = None):
        """Start a subprocess with stdout capture."""
        if name in self.processes and self.processes[name].poll() is None:
            return  # Already running
        
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd or self.base_dir,
            bufsize=1,
            env=full_env,
        )
        self.processes[name] = proc
        
        # Daemon thread to read stdout
        t = threading.Thread(target=self._read_output, args=(name, proc), daemon=True)
        t.start()
    
    def start_price_adapter(self):
        """Launch Price_adapter with correct CWD."""
        cmd = [sys.executable, "main.py"]
        cwd = os.path.join(self.base_dir, "Price_adapter")
        self.start_process("price_adapter", cmd, cwd=cwd)
    
    def start_trade_adapter(self):
        """Launch Trade_adapter from project root."""
        cmd = [sys.executable, "Trade_adapter.py"]
        self.start_process("trade_adapter", cmd)
    
    def start_strategy(self, strategy_id: str, script_path: str, symbol: str, trade_endpoint: str = "tcp://127.0.0.1:5555"):
        """Launch a user strategy as a subprocess."""
        cmd = [sys.executable, script_path]
        env = {
            "SIM_STRATEGY_ID": strategy_id,
            "SIM_SYMBOL": symbol,
            "SIM_TRADE_ENDPOINT": trade_endpoint,
            "SIM_CACHE_PATH": os.path.join(self.base_dir, "Temporary", "cache_candles"),
        }
        self.start_process(f"strategy_{strategy_id}", cmd, env=env)
    
    def get_status(self, name: str) -> str:
        if name not in self.processes:
            return "stopped"
        return "running" if self.processes[name].poll() is None else "error"
    
    def stop_all(self):
        for name, proc in self.processes.items():
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self.processes.clear()
    
    def stop_process(self, name: str):
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            del self.processes[name]
    
    def _read_output(self, name: str, proc: subprocess.Popen):
        try:
            for line in proc.stdout:
                self.log_buffer.add(name, line.strip())
        except Exception:
            pass
```

---

### 4.4 Task 4: Portfolio Enrichment Service

**File: `api/services/portfolio.py`**

This is the critical missing piece — computing displayable P&L from raw position data.

```python
from diskcache import Cache
from typing import Optional

class PortfolioService:
    def __init__(self, state_cache_path: str, liveprices_cache_path: str):
        self.state_cache = Cache(state_cache_path)
        self.prices_cache = Cache(liveprices_cache_path)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the latest price from live prices cache."""
        prices = self.prices_cache.get(f"prices:{symbol}")
        if prices and len(prices) > 0:
            return prices[-1]["price"]
        return None
    
    def get_enriched_positions(self) -> list[dict]:
        """Get all positions enriched with live P&L data."""
        positions = []
        for key in self.state_cache.iterkeys():
            if ":" not in key:
                continue
            strategy_id, symbol = key.split(":", 1)
            data = self.state_cache.get(key)
            if not data or data.get("qty", 0) == 0:
                continue
            
            qty = data["qty"]
            avg_price = data["avg_price"]
            current_price = self.get_current_price(symbol) or avg_price
            
            invested = qty * avg_price
            current_val = qty * current_price
            pnl_val = current_val - invested
            pnl_pct = (pnl_val / invested * 100) if invested != 0 else 0
            
            positions.append({
                "ticker": symbol,
                "initials": symbol[:2].upper(),
                "qty": qty,
                "avg_price": round(avg_price, 2),
                "current_price": round(current_price, 2),
                "invested": f"${invested:,.2f}",
                "current": f"${current_val:,.2f}",
                "pnl": f"{'+' if pnl_val >= 0 else ''}{pnl_val:,.2f}",
                "pnl_percent": f"{'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%",
                "strategy_id": strategy_id,
            })
        
        return positions
    
    def get_aggregate_stats(self, session_start_time: float) -> dict:
        """Compute aggregate P&L across all positions."""
        positions = self.get_enriched_positions()
        
        total_invested = sum(p["qty"] * p["avg_price"] for p in positions)
        total_current = sum(p["qty"] * p["current_price"] for p in positions)
        total_pnl = total_current - total_invested
        pnl_pct = (total_pnl / total_invested * 100) if total_invested != 0 else 0
        
        import time
        elapsed = int(time.time() - session_start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        trend = "up" if total_pnl > 0 else ("down" if total_pnl < 0 else "none")
        
        return {
            "session": {
                "pnl": f"{'+'if total_pnl>=0 else ''}${abs(total_pnl):,.2f}",
                "invested": f"${total_invested:,.2f}",
                "current": f"${total_current:,.2f}",
                "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                "trend": trend,
            },
            "global": {
                "total_pnl": f"{'+'if total_pnl>=0 else ''}${abs(total_pnl):,.2f}",
                "pnl_percent": f"{'+'if pnl_pct>=0 else ''}{pnl_pct:.2f}%",
                "active_algos": str(len(set(p["strategy_id"] for p in positions))),
                "algo_runtime": f"{hours}h {minutes}m",
                "pnl_trend": trend,
            }
        }
```

---

### 4.5 Task 5: Algorithm Store Service

**File: `api/services/algorithm_store.py`**

Manages the `algorithms/` directory and metadata stored in SQLite.

```python
import os
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from typing import Optional

class AlgorithmStore:
    def __init__(self, base_dir: str, db_path: str):
        self.algorithms_dir = os.path.join(base_dir, "algorithms")
        self.db_path = db_path
        os.makedirs(self.algorithms_dir, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS algorithms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                dependencies TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS algorithm_runs (
                run_id TEXT PRIMARY KEY,
                algorithm_id TEXT NOT NULL,
                date TEXT NOT NULL,
                pnl TEXT DEFAULT '$0.00',
                status TEXT DEFAULT 'Running',
                duration_seconds INTEGER DEFAULT 0,
                FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
            )
        """)
        conn.commit()
        conn.close()
    
    def list_algorithms(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        algos = conn.execute("SELECT * FROM algorithms ORDER BY created_at DESC").fetchall()
        result = []
        for algo in algos:
            runs = conn.execute(
                "SELECT * FROM algorithm_runs WHERE algorithm_id = ? ORDER BY date DESC",
                (algo["id"],)
            ).fetchall()
            result.append({
                "id": algo["id"],
                "name": algo["name"],
                "filename": algo["filename"],
                "dependencies": json.loads(algo["dependencies"]),
                "created_at": algo["created_at"],
                "history": [dict(r) for r in runs],
            })
        conn.close()
        return result
    
    def register(self, algo_id: str, name: str, filename: str, dependencies: list[str], file_content: bytes) -> dict:
        # Save the Python file
        filepath = os.path.join(self.algorithms_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)
        
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO algorithms (id, name, filename, dependencies, created_at) VALUES (?, ?, ?, ?, ?)",
            (algo_id, name, filename, json.dumps(dependencies), now)
        )
        conn.commit()
        conn.close()
        
        return {"id": algo_id, "name": name, "filename": filename, "dependencies": dependencies, "created_at": now}
    
    def delete(self, algo_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        algo = conn.execute("SELECT filename FROM algorithms WHERE id = ?", (algo_id,)).fetchone()
        if not algo:
            conn.close()
            return False
        
        filepath = os.path.join(self.algorithms_dir, algo[0])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        conn.execute("DELETE FROM algorithm_runs WHERE algorithm_id = ?", (algo_id,))
        conn.execute("DELETE FROM algorithms WHERE id = ?", (algo_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_script_path(self, algo_id: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        algo = conn.execute("SELECT filename FROM algorithms WHERE id = ?", (algo_id,)).fetchone()
        conn.close()
        if algo:
            return os.path.join(self.algorithms_dir, algo[0])
        return None
```

---

### 4.6 Task 6: WebSocket Event Broadcaster

**File: `api/websocket.py`**

```python
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from typing import Any

ws_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, event_type: str, data: Any):
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)

manager = ConnectionManager()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, optionally receive client messages
            data = await websocket.receive_text()
            # Could handle client commands here in the future
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

### 4.7 Task 7: Log Buffer with Formatting

**File: `api/services/log_buffer.py`**

```python
import threading
from datetime import datetime
from collections import deque

class LogBuffer:
    """Thread-safe circular log buffer with structured formatting."""
    
    # Color mapping for log sources
    SOURCE_COLORS = {
        "price_adapter": "text-blue-400",
        "trade_adapter": "text-yellow-400",
        "strategy": "text-green-400",
        "system": "text-purple-400",
        "error": "text-red-400",
    }
    
    def __init__(self, max_size: int = 500):
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._last_id = 0
    
    def add(self, source: str, message: str):
        """Add a log entry with automatic formatting."""
        with self._lock:
            self._last_id += 1
            color = self.SOURCE_COLORS.get(source, "text-gray-400")
            
            # Detect errors
            lower_msg = message.lower()
            if any(kw in lower_msg for kw in ["error", "exception", "traceback", "failed"]):
                color = self.SOURCE_COLORS["error"]
            
            entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "content": f"[{source.upper()}] {message}",
                "color": color,
            }
            self._buffer.append(entry)
    
    def get_all(self) -> list[dict]:
        with self._lock:
            return list(self._buffer)
    
    def get_since(self, since_time: str = None, limit: int = 100) -> list[dict]:
        with self._lock:
            entries = list(self._buffer)
            if since_time:
                entries = [e for e in entries if e["time"] > since_time]
            return entries[-limit:]
    
    def clear(self):
        with self._lock:
            self._buffer.clear()
```

---

### 4.8 Task 8: Settings Persistence

**File: `api/services/settings_store.py`**

```python
import os
import json
from typing import Any

DEFAULT_SETTINGS = {
    "currency": "USD",
    "theme": "dark",
    "simulated_latency_ms": 0,
    "commission_percent": 0.0,
    "leverage": 1,
    "auto_clear_logs": True,
    "system_alerts": True,
    "sound_effects": False,
    "terminal_font_size": 14,
}

class SettingsStore:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.paperquant")
        os.makedirs(config_dir, exist_ok=True)
        self.settings_path = os.path.join(config_dir, "settings.json")
        self._settings = self._load()
    
    def _load(self) -> dict:
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                saved = json.load(f)
            # Merge with defaults for any new keys
            return {**DEFAULT_SETTINGS, **saved}
        return dict(DEFAULT_SETTINGS)
    
    def _save(self):
        with open(self.settings_path, 'w') as f:
            json.dump(self._settings, f, indent=2)
    
    def get_all(self) -> dict:
        return dict(self._settings)
    
    def update(self, updates: dict) -> dict:
        for key, value in updates.items():
            if key in DEFAULT_SETTINGS:
                self._settings[key] = value
        self._save()
        return self.get_all()
```

---

### 4.9 Task 9: Session Manager (Orchestrator)

**File: `api/services/session_manager.py`**

This is the central orchestrator that ties everything together:

```python
import os
import json
import time
import shutil
import asyncio
from api.services.process_manager import ProcessManager
from api.services.portfolio import PortfolioService
from api.services.log_buffer import LogBuffer
from api.services.algorithm_store import AlgorithmStore
from api.services.settings_store import SettingsStore
from api.services.stats_tracker import StatsTracker

class SessionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Go up one more level if api/ is a subdirectory
        if os.path.basename(self.base_dir) == "api":
            self.base_dir = os.path.dirname(self.base_dir)
        
        self.temp_dir = os.path.join(self.base_dir, "Temporary")
        self.log_buffer = LogBuffer()
        self.pm = ProcessManager(self.base_dir, self.log_buffer)
        self.portfolio = PortfolioService(
            os.path.join(self.temp_dir, "state"),
            os.path.join(self.temp_dir, "cache_liveprices"),
        )
        self.algo_store = AlgorithmStore(
            self.base_dir,
            os.path.join(self.temp_dir, "paperquant.db"),
        )
        self.settings = SettingsStore()
        self.stats_tracker = StatsTracker()
        
        self.active_session = None  # dict with session info
        self._start_time = None
        self._push_task = None
    
    async def initialize(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        self.log_buffer.add("system", "PaperQuant API server initialized")
    
    async def shutdown(self):
        if self._push_task:
            self._push_task.cancel()
        self.pm.stop_all()
    
    async def start_session(self, watchlist, strategy_id=None, session_settings=None):
        if self.active_session:
            return None  # Already active
        
        # Write stocklist.json
        stocklist_path = os.path.join(self.temp_dir, "stocklist.json")
        tickers = [item["ticker"] for item in watchlist]
        with open(stocklist_path, "w") as f:
            json.dump(tickers, f)
        
        # Start adapters
        self.pm.start_price_adapter()
        self.pm.start_trade_adapter()
        
        self._start_time = time.time()
        session_id = f"sess_{time.strftime('%Y%m%d_%H%M%S')}"
        
        self.active_session = {
            "session_id": session_id,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "watchlist": tickers,
            "strategy_id": strategy_id,
        }
        
        # Start strategy if specified
        if strategy_id:
            script_path = self.algo_store.get_script_path(strategy_id)
            if script_path:
                for ticker in tickers:
                    self.pm.start_strategy(strategy_id, script_path, ticker)
        
        # Start WebSocket push loop
        self._push_task = asyncio.create_task(self._push_loop())
        
        self.log_buffer.add("system", f"Session {session_id} started with {len(tickers)} tickers")
        return self.active_session
    
    async def stop_session(self):
        if not self.active_session:
            return None
        
        session = self.active_session
        duration = int(time.time() - self._start_time) if self._start_time else 0
        
        if self._push_task:
            self._push_task.cancel()
            self._push_task = None
        
        self.pm.stop_all()
        self.active_session = None
        self._start_time = None
        
        self.log_buffer.add("system", f"Session {session['session_id']} stopped")
        return {"status": "stopped", "session_id": session["session_id"], "duration_seconds": duration}
    
    async def reset_session(self):
        await self.stop_session()
        
        # Clear temporary data (preserve stocklist structure)
        for item in os.listdir(self.temp_dir):
            path = os.path.join(self.temp_dir, item)
            if item == "stocklist.json":
                with open(path, "w") as f:
                    json.dump([], f)
                continue
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        
        # Recreate cache directories
        os.makedirs(os.path.join(self.temp_dir, "state"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "cache_candles"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "cache_liveprices"), exist_ok=True)
        
        self.log_buffer.clear()
        self.log_buffer.add("system", "Session reset complete")
        return {"status": "reset"}
    
    async def _push_loop(self):
        """Background task that broadcasts state via WebSocket every 2 seconds."""
        from api.websocket import manager
        while True:
            try:
                # Push positions
                positions = self.portfolio.get_enriched_positions()
                await manager.broadcast("positions_update", {"positions": positions})
                
                # Push stats
                if self._start_time:
                    stats = self.portfolio.get_aggregate_stats(self._start_time)
                    await manager.broadcast("stats_update", stats)
                
                # Push new logs (incremental)
                logs = self.log_buffer.get_all()
                if logs:
                    for log in logs[-5:]:  # Send last 5 new logs
                        await manager.broadcast("log", log)
                
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_buffer.add("error", f"Push loop error: {e}")
                await asyncio.sleep(5)
```

---

### 4.10 Task 10: Fix Existing Backend Files

#### 4.10.1 Fix `Price_adapter/live_fetch.py`

```diff
- import random
+ import time
+ import random

- import time
  # (remove duplicate/misplaced import)
```

Also fix mock collision:
```diff
  async def main(stocklist):
      cache = init_cache()
-     mock_task = asyncio.create_task(mock_generator(cache, stocklist))
+     mock_task = None
      
      try:
          ws = yf.AsyncWebSocket(verbose=False)
          # ... WebSocket setup ...
      except Exception:
-         # WebSocket unavailable, mock is already running
+         # WebSocket unavailable, start mock generator
+         mock_task = asyncio.create_task(mock_generator(cache, stocklist))
          await mock_task
```

#### 4.10.2 Fix `Indicators/trend.py`

```diff
+ import numpy as np
  import pandas as pd
  from .Candle_fetcher import candle_list
```

#### 4.10.3 Fix `Price_adapter/main.py` — Blocking Calls

```diff
- data = fetch_multiple_candles(stocklist, interval='1m', lookback_minutes=3)
+ data = await asyncio.to_thread(fetch_multiple_candles, stocklist, interval='1m', lookback_minutes=3)
```

#### 4.10.4 Fix `pyproject.toml`

```toml
[project]
name = "PaperQuant"
version = "0.2.0"
requires-python = ">=3.10,<4.0"

dependencies = [
    "yfinance (>=1.1.0,<2.0.0)",
    "diskcache (>=5.6.3,<6.0.0)",
    "pyzmq (>=27.1.0,<28.0.0)",
    "pandas (>=2.0.0,<3.0.0)",
    "numpy (>=1.24.0,<3.0.0)",
    "fastapi (>=0.115.0,<1.0.0)",
    "uvicorn[standard] (>=0.30.0,<1.0.0)",
    "websockets (>=12.0,<14.0)",
]
```

---

## 5. Route Implementations (Summary)

Each route file follows this pattern:

| Route File | Endpoints | Data Source |
|---|---|---|
| `routes/health.py` | `GET /api/health` | `ProcessManager.get_status()` |
| `routes/session.py` | `POST /api/session/start`, `POST /api/session/stop`, `POST /api/session/reset`, `GET /api/session/status` | `SessionManager` |
| `routes/positions.py` | `GET /api/positions`, `GET /api/positions/history` | `PortfolioService`, `order_history.csv` |
| `routes/stats.py` | `GET /api/stats`, `GET /api/stats/chart` | `PortfolioService.get_aggregate_stats()`, `StatsTracker` |
| `routes/algorithms.py` | `GET /api/algorithms`, `POST /api/algorithms`, `DELETE /api/algorithms/{id}`, `POST /api/algorithms/{id}/run`, `POST /api/algorithms/{id}/stop` | `AlgorithmStore`, `ProcessManager` |
| `routes/settings.py` | `GET /api/settings`, `PUT /api/settings` | `SettingsStore` |
| `routes/logs.py` | `GET /api/logs` | `LogBuffer` |
| `routes/market.py` | `GET /api/market/prices` | `DiskCache(cache_liveprices)` |

---

## 6. Verification Plan

### Automated Tests
```bash
# Unit tests for each service
python -m pytest tests/test_portfolio.py -v
python -m pytest tests/test_algorithm_store.py -v
python -m pytest tests/test_settings_store.py -v
python -m pytest tests/test_log_buffer.py -v

# Integration tests for API routes
python -m pytest tests/test_api_routes.py -v

# Full end-to-end test
python -m pytest tests/test_e2e.py -v
```

### Manual Verification
1. Start server: `python api_server.py`
2. Verify `GET /api/health` returns correct JSON
3. Start session with `POST /api/session/start` and verify adapters launch
4. Check `GET /api/positions` returns enriched position data
5. Upload algorithm via `POST /api/algorithms`
6. Connect WebSocket client and verify events stream
7. Stop session and verify clean shutdown

### CI/CD Quality Gates
```bash
# Phase 1: Code Quality
ruff check .
mypy api/ --strict
python -m py_compile api_server.py

# Phase 2: Tests
python -m pytest tests/ -v --tb=short
```

---

## 7. Migration Notes

- **`UI/Wrapper/main.py` is DEPRECATED** — it will not be deleted yet but is no longer the entry point
- The existing `Handler.py`, `Trade_adapter.py`, and `Price_adapter/` are **preserved** with minimal changes
- The `api/` package is a **new layer on top** of the existing architecture
- All DiskCache paths and ZMQ endpoints remain unchanged
- The `algorithms/` directory is a new addition for user strategy storage
