# API Specification & Documentation

## 1. Goal

This document defines every endpoint, data schema, WebSocket event, and error contract between the Python backend (FastAPI sidecar) and the React frontend. This defines a standard HTTP + WebSocket architecture suitable for Tauri packaging.

---

## 2. Architecture

### HTTP/WS Architecture
```
┌──────────────┐     HTTP/WS      ┌──────────────────────────────────────┐
│  React       │ ←──────────────→ │  FastAPI Server (api_server.py)      │
│  Frontend    │  localhost:PORT  │                                      │
│  (Tauri      │                  │  ┌─ ProcessManager ──────────────┐   │
│   WebView)   │                  │  │  Price_adapter (subprocess)   │   │
│ └──────────────┘                  │  │  Trade_adapter (subprocess)   │   │
                                  │  │  Strategy runners (subproc)   │   │
                                  │  └───────────────────────────────┘   │
                                  │                                      │
                                  │  DiskCache (shared state)            │
                                  │  SQLite (candle history & trades)    │
                                  └──────────────────────────────────────┘
```

---

## 3. API Server Specification

### 3.1 Server Configuration

| Property | Value |
|---|---|
| Framework | FastAPI (Python) |
| Host | `127.0.0.1` (localhost only — no network exposure) |
| Port | Dynamic (find available port, write to `~/.paperquant/port`) |
| CORS | Allow origin `tauri://localhost` and `http://localhost:*` |
| Transport | HTTP/1.1 + WebSocket (single uvicorn server) |
| Auth | None (localhost-only, single-user desktop app) |

### 3.2 Health & Lifecycle

#### `GET /api/health`
Frontend calls this on startup to verify backend is alive.

**Response** `200 OK`:
```json
{
  "status": "ok",
  "version": "0.2.0",
  "uptime_seconds": 142,
  "adapters": {
    "price_adapter": "running" | "stopped" | "error",
    "trade_adapter": "running" | "stopped" | "error"
  }
}
```

---

### 3.3 Session Management

#### `POST /api/session/start`
Starts a new trading session. Writes `stocklist.json`, launches Price_adapter, Trade_adapter, and optionally a strategy subprocess.

**Request Body**:
```json
{
  "watchlist": [
    { "ticker": "AAPL", "capital": 1000.0 },
    { "ticker": "MSFT", "capital": 2000.0 }
  ],
  "strategy_id": "my_rsi_strategy",   // optional — null for manual session
  "settings": {
    "simulated_latency_ms": 0,
    "commission_percent": 0.0,
    "leverage": 1
  }
}
```

**Response** `200 OK`:
```json
{
  "status": "started",
  "session_id": "sess_20260922_061100",
  "started_at": "2026-09-22T06:11:00Z"
}
```

**Response** `409 Conflict` (session already active):
```json
{
  "error": "session_active",
  "message": "A session is already running. Stop it first."
}
```

---

#### `POST /api/session/stop`
Gracefully stops all subprocesses (Price_adapter, Trade_adapter, strategy).

**Response** `200 OK`:
```json
{
  "status": "stopped",
  "session_id": "sess_20260922_061100",
  "duration_seconds": 3600
}
```

---

#### `POST /api/session/reset`
Stops all processes, clears `Temporary/` (except preserves `stocklist.json` as empty), restarts adapters fresh.

**Response** `200 OK`:
```json
{
  "status": "reset",
  "message": "Session data cleared and adapters restarted."
}
```

---

#### `GET /api/session/status`
Returns current session state.

**Response** `200 OK`:
```json
{
  "active": true,
  "session_id": "sess_20260922_061100",
  "started_at": "2026-09-22T06:11:00Z",
  "uptime_seconds": 3600,
  "strategy": {
    "id": "my_rsi_strategy",
    "name": "RSI Momentum Strategy",
    "status": "running"
  },
  "watchlist": ["AAPL", "MSFT"],
  "adapters": {
    "price_adapter": "running",
    "trade_adapter": "running"
  }
}
```

---

### 3.4 Positions & Portfolio

#### `GET /api/positions`
Returns all current open positions across all strategies.

**Response** `200 OK`:
```json
{
  "positions": [
    {
      "ticker": "AAPL",
      "initials": "AA",
      "qty": 10,
      "avg_price": 185.50,
      "current_price": 187.20,
      "invested": "$1,855.00",
      "current": "$1,872.00",
      "pnl": "+$17.00",
      "pnl_percent": "+0.92%",
      "strategy_id": "my_rsi_strategy"
    }
  ]
}
```

---

#### `GET /api/positions/history`
Returns historical trade log from SQLite database (`trades` table).

**Response** `200 OK`:
```json
{
  "trades": [
    {
      "timestamp": "2026-09-22T06:15:00Z",
      "strategy_id": "my_rsi_strategy",
      "symbol": "AAPL",
      "side": "buy",
      "qty": 10,
      "price": 185.50,
      "order_type": "market"
    }
  ]
}
```

---

### 3.5 Portfolio Statistics (for Dashboard)

#### `GET /api/stats`
Computes aggregate portfolio statistics for the active session.

**Response** `200 OK`:
```json
{
  "session": {
    "pnl": "+$42.50",
    "pnl_percent": "+1.42%",
    "invested": "$3,000.00",
    "current": "$3,042.50",
    "uptime": "01:23:45",
    "trend": "up"
  },
  "global": {
    "total_pnl": "+$42.50",
    "pnl_percent": "+1.42%",
    "active_algos": "1",
    "algo_runtime": "1h 23m",
    "pnl_trend": "up"
  }
}
```

---

#### `GET /api/stats/chart`
Returns P&L time series for the performance chart (SVG path generation done frontend-side).

**Response** `200 OK`:
```json
{
  "timestamps": ["2026-09-22T06:11:00Z", "2026-09-22T06:12:00Z", ...],
  "pnl_values": [0.0, 1.20, -0.50, 3.40, ...],
  "interval_seconds": 60
}
```

---

### 3.6 Algorithm Management

#### `GET /api/algorithms`
Lists all registered algorithm scripts.

**Response** `200 OK`:
```json
{
  "algorithms": [
    {
      "id": "my_rsi_strategy",
      "name": "RSI Momentum Strategy",
      "filename": "rsi_strategy.py",
      "dependencies": ["numpy", "pandas"],
      "created_at": "2026-09-15T10:30:00Z",
      "history": [
        {
          "run_id": "run_001",
          "date": "2026-09-20",
          "pnl": "+$12.50",
          "status": "Completed",
          "duration_seconds": 7200
        }
      ]
    }
  ]
}
```

---

#### `POST /api/algorithms`
Registers a new algorithm from an uploaded `.py` file.

**Request**: `multipart/form-data`
- `file`: The `.py` strategy script
- `name`: Display name (string)
- `dependencies`: Comma-separated dependency list (string)

**Response** `201 Created`:
```json
{
  "id": "my_rsi_strategy",
  "name": "RSI Momentum Strategy",
  "filename": "rsi_strategy.py",
  "dependencies": ["numpy", "pandas"],
  "created_at": "2026-09-22T06:30:00Z"
}
```

---

#### `DELETE /api/algorithms/{algorithm_id}`
Removes a registered algorithm.

**Response** `200 OK`:
```json
{
  "status": "deleted",
  "id": "my_rsi_strategy"
}
```

---

#### `POST /api/algorithms/{algorithm_id}/run`
Starts running an algorithm against the active session.

**Request Body**:
```json
{
  "symbol": "AAPL"
}
```

**Response** `200 OK`:
```json
{
  "status": "started",
  "run_id": "run_002",
  "algorithm_id": "my_rsi_strategy",
  "symbol": "AAPL"
}
```

---

#### `POST /api/algorithms/{algorithm_id}/stop`
Stops a running algorithm.

**Response** `200 OK`:
```json
{
  "status": "stopped",
  "run_id": "run_002"
}
```

---

### 3.7 Settings

#### `GET /api/settings`
Returns persisted application settings.

**Response** `200 OK`:
```json
{
  "currency": "USD",
  "theme": "dark",
  "simulated_latency_ms": 0,
  "commission_percent": 0.0,
  "leverage": 1,
  "auto_clear_logs": true,
  "system_alerts": true,
  "sound_effects": false,
  "terminal_font_size": 14
}
```

---

#### `PUT /api/settings`
Updates application settings. Partial update — only sends changed fields.

**Request Body** (partial):
```json
{
  "commission_percent": 0.1,
  "leverage": 2
}
```

**Response** `200 OK`:
```json
{
  "status": "updated",
  "settings": { /* full settings object */ }
}
```

---

### 3.8 Logs (Polling Fallback)

#### `GET /api/logs`
Returns recent log entries. Used as fallback if WebSocket is unavailable.

**Query Parameters**:
- `since` (optional): ISO timestamp — only return logs after this time
- `limit` (optional, default 100): Max entries to return

**Response** `200 OK`:
```json
{
  "logs": [
    {
      "time": "06:11:42",
      "content": "[PriceAdapter] Fetched 2 tickers: AAPL, MSFT",
      "color": "text-blue-400"
    }
  ]
}
```

---

### 3.9 Market Data

#### `GET /api/market/prices`
Returns latest prices for all watched symbols.

**Response** `200 OK`:
```json
{
  "prices": {
    "AAPL": {
      "price": 187.20,
      "timestamp": "2026-09-22T06:15:30Z",
      "source": "live" | "mock"
    }
  }
}
```

---

## 4. WebSocket Specification

### 4.1 Connection

```
ws://127.0.0.1:{PORT}/ws
```

The WebSocket replaces the `evaluate_js()` polling loop. The server pushes events to the client in real-time.

### 4.2 Event Format

All WebSocket messages are JSON with a `type` field:

```json
{
  "type": "event_type",
  "data": { ... },
  "timestamp": "2026-09-22T06:15:30Z"
}
```

### 4.3 Event Types

| Event Type | Direction | Payload | Frontend Action |
|---|---|---|---|
| `positions_update` | Server → Client | `{ positions: Position[] }` | `setPositions(data.positions)` |
| `log` | Server → Client | `{ time: string, content: string, color: string }` | `addLog(data)` |
| `stats_update` | Server → Client | `{ session: SessionStats, global: GlobalStats }` | `setStats(data.session)`, `setGlobalStats(data.global)` |
| `strategy_update` | Server → Client | `{ name: string, status: string }` | `setStrategyName(data.name)` |
| `system_pulse` | Server → Client | `{ time: string, msg: string, color: string }` | `addSystemPulse(data)` |
| `chart_update` | Server → Client | `{ pnl_values: number[], timestamps: string[] }` | Update SVG chart |
| `price_tick` | Server → Client | `{ symbol: string, price: number, ts: string }` | Update price display |
| `trade_executed` | Server → Client | `{ symbol: string, side: string, qty: number, price: number }` | Notification + log |
| `adapter_status` | Server → Client | `{ adapter: string, status: string }` | Update health indicator |
| `session_ended` | Server → Client | `{ reason: string }` | Navigate to setup view |
| `error` | Server → Client | `{ code: string, message: string }` | Show error notification |

### 4.4 Push Interval

| Event | Frequency |
|---|---|
| `positions_update` | Every 2 seconds (when session active) |
| `stats_update` | Every 2 seconds (when session active) |
| `log` | Immediately on new log entry (debounced 100ms) |
| `price_tick` | On every tick (throttled to 1/sec per symbol) |
| `chart_update` | Every 60 seconds |
| `system_pulse` | On event (adapter start/stop, errors, etc.) |
| `trade_executed` | Immediately on execution |

---

## 5. Data Schemas (Shared Types)

These schemas are the **single source of truth** for both backend (Pydantic models) and frontend (TypeScript interfaces).

### 5.1 Position

```typescript
// Frontend: src/types/api.ts
interface Position {
  ticker: string;        // e.g. "AAPL"
  initials: string;      // e.g. "AA" (first 2 chars of ticker)
  qty: number;           // e.g. 10
  avg_price: number;     // e.g. 185.50
  current_price: number; // e.g. 187.20
  invested: string;      // e.g. "$1,855.00" (formatted)
  current: string;       // e.g. "$1,872.00" (formatted)
  pnl: string;           // e.g. "+$17.00" (formatted, with +/- prefix)
  pnl_percent: string;   // e.g. "+0.92%"
  strategy_id: string;   // e.g. "my_rsi_strategy"
}
```

```python
# Backend: api/schemas.py
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
```

### 5.2 LogEntry

```typescript
interface LogEntry {
  time: string;     // e.g. "06:11:42"
  content: string;  // e.g. "[PriceAdapter] Fetched AAPL"
  color: string;    // e.g. "text-blue-400"
}
```

### 5.3 Algorithm

```typescript
interface Algorithm {
  id: string;
  name: string;
  filename: string;
  dependencies: string[];
  created_at: string;     // ISO 8601
  history: AlgorithmRun[];
}

interface AlgorithmRun {
  run_id: string;
  date: string;
  pnl: string;
  status: 'Completed' | 'Stopped' | 'Failed';
  duration_seconds: number;
}
```

### 5.4 SessionStats

```typescript
interface SessionStats {
  pnl: string;       // e.g. "+$42.50"
  invested: string;  // e.g. "$3,000.00"
  current: string;   // e.g. "$3,042.50"
  uptime: string;    // e.g. "01:23:45"
  trend: 'up' | 'down' | 'none';
}
```

### 5.5 GlobalStats

```typescript
interface GlobalStats {
  total_pnl: string;      // e.g. "+$42.50"
  pnl_percent: string;    // e.g. "+1.42%"
  active_algos: string;   // e.g. "1"
  algo_runtime: string;   // e.g. "1h 23m"
  pnl_trend: 'up' | 'down' | 'none';
}
```

### 5.6 Settings

```typescript
interface Settings {
  currency: string;              // "USD" | "EUR" | "GBP" | "INR"
  theme: string;                 // "dark" (only supported for now)
  simulated_latency_ms: number;  // 0, 50, 100, 250, 500
  commission_percent: number;    // 0.0, 0.05, 0.1, 0.25
  leverage: number;              // 1, 2, 5, 10
  auto_clear_logs: boolean;
  system_alerts: boolean;
  sound_effects: boolean;
  terminal_font_size: number;    // 12, 14, 16
}
```

---

## 6. Error Contract

All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": { ... }   // optional
}
```

### Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `session_active` | 409 | Trying to start a session when one is already running |
| `no_active_session` | 400 | Trying to stop/interact with session when none is running |
| `algorithm_not_found` | 404 | Algorithm ID doesn't exist |
| `algorithm_already_running` | 409 | Algorithm is already executing |
| `invalid_ticker` | 400 | Ticker symbol is not valid / not found on Yahoo Finance |
| `file_invalid` | 400 | Uploaded file is not a valid Python script |
| `adapter_error` | 500 | Price or Trade adapter crashed |
| `internal_error` | 500 | Unexpected server error |
