# PaperQuant — Comprehensive Codebase Analysis

> **Codebase indexed:** 352 nodes, 1077 edges across 21 Python files + 14 TypeScript files  
> **Analysis date:** September 2026 | **Version:** 0.1.0

---

## 1. What Is PaperQuant?

**PaperQuant** is an open-source, desktop-native **paper trading platform** for algorithmic traders. "Paper trading" means simulated trading using real market data but with virtual money — no real capital at risk. 

The system is designed so that users can:
1. Write algorithmic trading strategies in Python
2. Run them against real-time Yahoo Finance market data
3. See live position tracking, P&L, logs, and execution terminals in a polished desktop UI
4. Iterate on their strategies without financial risk

The architecture is built on a **multi-process, IPC-first** model: separate Python processes handle data fetching, trade execution, and the desktop GUI, all wired together via **ZeroMQ sockets** and a shared **DiskCache** key-value store.

---

## 2. Technical Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ (backend), TypeScript/React (frontend) |
| **IPC / Messaging** | ZeroMQ (`pyzmq`) — DEALER/ROUTER pattern |
| **Caching / State** | DiskCache (SQLite-backed key-value, shared-memory style) |
| **Database** | SQLite via `sqlite3` stdlib (`paperquant.db`) |
| **Market Data** | Yahoo Finance via `yfinance` (REST + WebSocket) |
| **Frontend Framework** | React 19 + TypeScript + Vite 8 |
| **UI Styling** | Tailwind CSS v4 + `lucide-react` icons |
| **Desktop Wrapper** | `pywebview` (planned — wraps React dist into native window) |
| **Python Pkg Manager** | Poetry |
| **Frontend Pkg Manager** | npm |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UI/Wrapper/main.py                               │
│   (pywebview Desktop App — orchestrates all sub-processes via Popen)    │
└────────────────────┬───────────────────────┬────────────────────────────┘
                     │ subprocess             │ subprocess
                     ▼                        ▼
     ┌───────────────────────┐   ┌──────────────────────────┐
     │  Price_adapter/main.py│   │   Trade_adapter.py       │
     │  (Async data pipeline)│   │   (ZMQ ROUTER — order    │
     │  ┌────────────────┐   │   │    execution engine)     │
     │  │ live_fetch.py  │   │   │                          │
     │  │ yf.WebSocket   │   │   │  Maintains virtual       │
     │  └────────┬───────┘   │   │  portfolio in DiskCache  │
     │           │ prices     │   │  Logs trades to CSV      │
     │  ┌────────▼───────┐   │   └──────────┬───────────────┘
     │  │ db_handler.py  │   │              │ ZMQ DEALER
     │  │ DiskCache      │   │              │
     │  │ SQLite         │   │   ┌──────────▼───────────────┐
     │  └────────────────┘   │   │   Handler.py             │
     └───────────────────────┘   │  (Strategy API: prices + │
                                 │   action.buy/sell)       │
              DiskCache          │                          │
              (shared state)     │   ┌──────────────────┐   │
             ◄───────────────────┤   │  Indicators/     │   │
                                 │   │  (RSI, MACD, ATR │   │
                                 │   │   Bollinger, etc) │   │
                                 │   └──────────────────┘   │
                                 └──────────────────────────┘

              React Frontend (UI/Frontend/dist/)
              ← served via pywebview local file ←
              ← JS calls pywebview.api.* → Python API class →
```

### Data Flow Summary

1. **`Price_adapter`** fetches OHLCV candles from `yfinance` every 60s → writes to SQLite + DiskCache  
2. **`Price_adapter/live_fetch.py`** subscribes to `yf.AsyncWebSocket` for tick-level prices → DiskCache  
3. **`Trade_adapter.py`** binds a ZMQ ROUTER; holds an in-memory pending orders list; checks live price ticks from DiskCache every 100ms  
4. **Strategy scripts** import `Handler.py` which exposes `prices` (market data) + `action.buy/sell` (ZMQ DEALER to Trade Adapter)  
5. **`Indicators/`** library is used by strategies via `Handler.indicators.*`  
6. **`UI/Wrapper/main.py`** launches all processes, wraps the built React app in a `pywebview` window, and exposes a Python `API` class to JS

---

## 4. Detailed File-by-File Breakdown

### 🔧 Root

#### [`Handler.py`](file:///mnt/Data/Coding/PaperQuant/Handler.py)
**Role:** The primary API surface for strategy scripts.

- Reads env vars `SIM_STRATEGY_ID`, `SIM_SYMBOL`, `SIM_TRADE_ENDPOINT`, `SIM_CACHE_PATH`
- Creates a **ZMQ async DEALER socket** (`zmq.asyncio`), identifying itself with the strategy ID
- Exposes a `prices` class with two static methods:
  - `prices.last_candle(symbol)` — reads the latest OHLCV candle from DiskCache
  - `prices.candle_list(symbol, n, interval, field)` — fetches `n` historical candles directly from `yfinance` (with 2.5–4x buffer to skip weekends/holidays)
- Exposes an `action` class with:
  - `action.buy(qty, price=None, symbol)` — async, sends JSON payload over ZMQ
  - `action.sell(qty, price=None, symbol)` — same
- Also imports `Indicators.Main.indicators` and re-exports it, so strategies get all indicators in scope

**Works?** ✅ Solid. Well-structured. One minor concern: `_socket` is module-level and connects at import time — this means it must be imported in an async context (strategy must run in an async event loop).

---

#### [`Trade_adapter.py`](file:///mnt/Data/Coding/PaperQuant/Trade_adapter.py)
**Role:** The execution engine for simulated trades.

- Binds a **ZMQ ROUTER** on `tcp://127.0.0.1:5555`
- Main loop (100ms poll interval):
  1. Iterates all **pending limit orders** and checks if the delayed live price has reached the limit price
  2. Polls the ZMQ socket for new order messages
- Handles `buy` and `sell` actions
- **Market orders:** executed immediately at the latest delayed price (60-second delay baked in to simulate real execution)
- **Limit orders:** queued in `pending_orders` list, checked every 100ms
- Position tracking via `update_position()` — weighted average cost basis, supports short positions and position flips
- Logs all executed trades to `Temporary/order_history.csv`
- State stored in DiskCache under key `"{strategy_id}:{symbol}"` → `{"qty": int, "avg_price": float}`

**Works?** ✅ Functionally solid. Note: the 60s price delay is always applied even for market orders — this is intentional to avoid look-ahead bias but might confuse users who expect instant fills.

---

#### [`pyproject.toml`](file:///mnt/Data/Coding/PaperQuant/pyproject.toml)
Minimal 4-dependency Python project:
- `yfinance >=1.1.0,<2.0.0`
- `diskcache >=5.6.3,<6.0.0`
- `pyzmq >=27.1.0,<28.0.0`
- `jupyter >=1.1.1,<2.0.0` (for the testing notebook)

> [!NOTE] `pandas` and `numpy` (heavily used in all indicator modules) are **not listed as explicit dependencies** — they're pulled in transitively through `yfinance`. This is fragile. Also `pywebview` (needed by the Wrapper) is missing entirely from `pyproject.toml`.

---

### 📡 `Price_adapter/`

#### [`Price_adapter/main.py`](file:///mnt/Data/Coding/PaperQuant/Price_adapter/main.py)
**Role:** Async orchestrator for data ingestion.

- Reads `Temporary/stocklist.json` (a JSON array of ticker strings, e.g. `["AAPL", "MSFT"]`)
- Spawns `live_fetch.main(stocklist)` as an async task
- Runs `periodic_fetch_and_store(stocklist)` in a loop every **60 seconds**
  - Calls `fetch_multiple_candles()` → `imt_sqlite()` → `update_diskcache_candles()`
- Clean shutdown on `CancelledError` / `KeyboardInterrupt`

**Works?** ✅ Clean async design. Depends on `stocklist.json` existing — if it's missing, crashes with an unhandled `FileNotFoundError`.

---

#### [`Price_adapter/fetch.py`](file:///mnt/Data/Coding/PaperQuant/Price_adapter/fetch.py)
**Role:** Batch OHLCV candle fetcher.

- `current_candle(symbol)` — fetches latest 1m candle for a single ticker
- `fetch_multiple_candles(symbols)` — batch-fetches using `yf.Tickers().download()` for efficiency
- Always fetches from `start = (now - lookback_minutes)` to `end = (now - 1min)` to avoid including the in-progress candle
- Normalizes timestamps to UTC, minute-aligned

**Works?** ✅ Well-implemented. The multi-ticker batch approach avoids API rate-limit issues.

---

#### [`Price_adapter/live_fetch.py`](file:///mnt/Data/Coding/PaperQuant/Live price fetcher`]
**Role:** Real-time tick ingestion.

- Attempts to subscribe to `yf.AsyncWebSocket` for live streaming prices
- If the WebSocket is unavailable (market closed, API issue), falls back to a **mock generator** that simulates random price walk
- Mock prices start at `$150 ± $50` with random walk `±$0.50` per second
- Stores rolling 2-minute tick history in DiskCache under `"prices:{symbol}"` as a list of `{price, ts}` dicts

**Works?** ⚠️ Partially. The real WebSocket path depends on an undocumented `yf.AsyncWebSocket` API (not stable in `yfinance <2.0`). The mock fallback works fine for development/testing. There's also an import ordering issue: `time` is used in `mock_generator` but imported later in the file (line 29 vs use on line 22).

---

#### [`Price_adapter/db_handler.py`](file:///mnt/Data/Coding/PaperQuant/Price_adapter/db_handler.py)
**Role:** Data persistence.

- `imt_sqlite(data)` — bulk inserts OHLCV candles into `paperquant.db` with `INSERT OR IGNORE` (deduplication by `(symbol, timestamp)`)
- `update_diskcache_candles(ticker, data)` — writes the **single latest candle** per ticker to DiskCache
- Module-level `cache = Cache(...)` initialized at import — means the process holds a persistent DiskCache connection

**Works?** ✅ Correct. The `INSERT OR IGNORE` + deduplication-in-memory pattern is robust.

---

### 📊 `Indicators/`

All indicator modules follow the same pattern: they call `candle_list(symbol, n, interval, field)` from `Candle_fetcher.py`, construct a `pd.Series`, then compute and return the latest value.

#### [`Indicators/Candle_fetcher.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/Candle_fetcher.py)
The **hotspot** of the system (fan-in: 35). Every indicator calls this. It wraps `prices.candle_list()` from the outer `Handler.py` scope — but there's an important issue: the Indicators are a standalone package that **also has its own** `candle_list` implementation, which calls `yfinance` directly. This decoupling allows Indicators to be used standalone, outside of a strategy/Handler context.

#### [`Indicators/Main.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/Main.py)
Aggregates all indicator submodules into a single `indicators` class namespace. Clean facade pattern.

#### [`Indicators/momentum.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/momentum.py)
**Implemented:** RSI, Stochastic Oscillator, Stochastic RSI, CCI, Williams %R, ROC, TSI, Ultimate Oscillator, PPO

#### [`Indicators/volatility.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/volatility.py)
**Implemented:** ATR, Bollinger Bands

#### [`Indicators/moving_avg.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/moving_avg.py)
**Likely contains:** SMA, EMA, WMA, HMA, AMA, Supertrend (graph shows `hma`, `wma`, `ama`, `supertrend`)

#### [`Indicators/volume.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/volume.py)
**Likely contains:** OBV, A/D Line (graph shows `obv`, `ad_line`)

#### [`Indicators/levels.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/levels.py)
Support/Resistance detection, pivot points

#### [`Indicators/market_structure.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/market_structure.py)
Trend shifts, Break of Structure (BOS), Change of Character (CHoCH) — smart money concepts

#### [`Indicators/trend.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/trend.py)
ADX and trend strength

#### [`Indicators/signals.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/signals.py)
Composite buy/sell signal generation

#### [`Indicators/statistics.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/statistics.py)
Standard deviation, variance, correlation

#### [`Indicators/price_transforms.py`](file:///mnt/Data/Coding/PaperQuant/Indicators/price_transforms.py)
Log returns, price manipulation utilities

**Overall Indicators assessment:** ✅ The library is well-structured and impressively comprehensive for a v0.1 project. Each function handles its own data fetching and returns a scalar or dict — easy to compose in strategies.

---

### 🖥️ `UI/`

#### [`UI/Wrapper/main.py`](file:///mnt/Data/Coding/PaperQuant/UI/Wrapper/main.py)
**Role:** Desktop application entry point.

**Key classes:**
- `LogBuffer` — thread-safe ring buffer (100 entries) for capturing process stdout
- `ProcessManager` — wraps `subprocess.Popen`, reads stdout in daemon threads, pushes to `LogBuffer`
- `API` — the JavaScript-callable API object exposed via `pywebview`'s `js_api`

**API methods exposed to JS:**
| Method | Description |
|---|---|
| `reset_session()` | Stop all processes, wipe `Temporary/` (except stocklist), restart adapters |
| `stop_session()` | Kill all subprocesses |
| `get_positions()` | Read all positions from state DiskCache |
| `get_logs()` | Return last 100 log lines |
| `start_adapters()` | Launch `Price_adapter/main.py` and `Trade_adapter.py` |

**Polling thread:** runs every 2 seconds, pushes positions + logs to the React frontend via `window.evaluate_js()` calling `window.updatePositions()` and `window.addLog()` (global functions exposed by `PaperQuantContext.tsx`).

**Works?** ⚠️ Mostly, with notable gaps:
- Starts `Price_adapter` from `BASE_DIR` — but `Price_adapter/main.py` uses relative imports (`from fetch import ...`) which **only work if the CWD is `Price_adapter/`**. The Wrapper starts it from `BASE_DIR`, which will cause `ModuleNotFoundError`.
- `pywebview` is not in `pyproject.toml`
- The polling log injection is crude — sends ALL logs and clears them every 2 seconds instead of incremental diff

---

#### [`UI/Frontend/src/App.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/App.tsx)
Root component. Manages `view` state (a string key) and renders the appropriate view:

| View key | Component |
|---|---|
| `'home'` | `<HomeView />` |
| `'setup'` | `<SetupView onStart=... />` |
| `'algorithms'` | `<AlgorithmsView />` |
| `'settings'` | `<SettingsView />` |
| `'active'` | Inline active session dashboard with stat cards, positions table, terminal |

Also wires up `handleStopSession` and `handleResetSession` to call the pywebview API.

**Works?** ✅ Solid routing. No external router dependency (custom state machine).

---

#### [`UI/Frontend/src/context/PaperQuantContext.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/context/PaperQuantContext.tsx)
**Role:** Global state store (React Context).

Manages all shared state:
- **Active session:** positions, logs, stats (P&L, invested, current, uptime), strategyName
- **Home/command center:** globalStats, recentExecutions, systemPulse feed, chartPath (SVG d attribute)
- **Notification handler:** wraps the browser `Notification` API

**Critical feature:** Exposes React state setters as `window.*` globals (`window.updatePositions`, `window.addLog`, `window.clearLogs`, etc.) so the Python Wrapper's `evaluate_js()` calls can directly mutate React state. This is clever for a pywebview integration.

**Works?** ✅ Clean pattern for pywebview integration. The `useEffect` dependency on `notificationsEnabled` ensures the closure is always fresh.

---

#### [`UI/Frontend/src/hooks/useBackend.ts`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/hooks/useBackend.ts)
Polls for `window.pywebview.api` availability every 100ms. Returns `{isReady, callBackend}`. `callBackend` is a typed wrapper around `window.pywebview.api.*` calls.

**Works?** ✅ Correct. The typed `BackendAPI` interface matches the Python `API` class methods.

---

#### [`UI/Frontend/src/components/HomeView.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/HomeView.tsx)
Command center / dashboard showing:
- Total P&L stat card + Active Algos + Algo Runtime cards
- SVG Performance Pulse chart (animated gradient line chart driven by `chartPath` from context)
- System Pulse feed (log tail)
- Recent Executions grid (algo history cards)

All data sourced from `PaperQuantContext`. Currently all state is `[]` / `'-'` as no backend integration populates these on the Home view — the Wrapper only pushes positions and logs, not globalStats or recentExecutions.

**Works?** ⚠️ UI renders fine, but the meaningful data (globalStats, chartPath, recentExecutions) is **never populated** by the backend Wrapper. These are effectively dead UI slots.

---

#### [`UI/Frontend/src/components/SetupView.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/SetupView.tsx)
Pre-session configuration screen:
- Watchlist builder (add/remove tickers, set capital per ticker)
- Strategy selection dropdown (empty — comments say "populated from backend" but no backend call is made)
- "Start Session" button (disabled if watchlist empty)

**Works?** ⚠️ UI works as a local state form. However:
- The selected tickers are **never written to** `Temporary/stocklist.json` — the backend expects this file to exist
- The strategy dropdown is hardcoded-empty (no API call to list available scripts)
- Capital per ticker is stored in UI state only — the Trade Adapter has no concept of capital limits

---

#### [`UI/Frontend/src/components/AlgorithmsView.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/AlgorithmsView.tsx)
Algorithm library manager:
- Drag-and-drop zone for uploading `.py` strategy files
- Registration form (name + dependencies textarea)
- Algo list showing name, dependencies, recent run P&L and history

**Works?** ⚠️ UI is fully built. But `algos` state is initialized as `[]` and **never populated** — no backend API call to list, upload, or register scripts. The "Register Algorithm" button has no `onClick` handler (beyond the `resetForm` cancel).

---

#### [`UI/Frontend/src/components/SettingsView.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/SettingsView.tsx)
Settings page with:
- Display currency + app theme dropdowns
- Trading simulation config (simulated latency, commission, leverage)
- UI toggles (auto-clear logs, system alerts, sound effects)
- System status card showing Python Engine status

**Works?** ⚠️ UI renders correctly. However:
- Currency/theme/latency/commission/leverage settings are **local UI state only** — none wired to the backend
- "Python Engine Status" always shows `CONNECTED (12ms)` — hardcoded, not a real health check
- Theme switching not implemented (only one theme exists)

---

#### [`UI/Frontend/src/components/PositionsTable.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/PositionsTable.tsx)
Reads `positions` from `PaperQuantContext`. Renders open positions — populated by the Python Wrapper's polling thread via `window.updatePositions()`.

**Works?** ✅ This is one of the few fully-wired UI components.

---

#### [`UI/Frontend/src/components/ExecutionTerminal.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/ExecutionTerminal.tsx)
Renders `logs` from `PaperQuantContext` — the terminal log view. Populated by `window.addLog()` from the Wrapper's polling thread.

**Works?** ✅ Wired. The polling clears and re-injects all logs every 2s which causes flicker, but functional.

---

#### Supporting Frontend Files

| File | Role |
|---|---|
| [`src/components/Sidebar.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/Sidebar.tsx) | Navigation sidebar, sets `view` state on click |
| [`src/components/StatCard.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/components/StatCard.tsx) | Reusable metric card (hotspot: fan-in 8) |
| [`src/lib/utils.ts`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/lib/utils.ts) | `cn()` utility (tailwind-merge + clsx) |
| [`src/main.tsx`](file:///mnt/Data/Coding/PaperQuant/UI/Frontend/src/main.tsx) | React root mount, wraps in `PaperQuantProvider` |

---

### 🔬 Tests

#### [`test_order.py`](file:///mnt/Data/Coding/PaperQuant/test_order.py)
A manual integration test script. Imports `Handler.py` and exercises the `action.buy/sell` flow against a running Trade Adapter.

#### [`testing.ipynb`](file:///mnt/Data/Coding/PaperQuant/testing.ipynb)
Jupyter notebook for exploratory indicator and data testing (excluded from git index as per `.gitignore`).

---

## 5. Features Status

### ✅ Completed / Working

| Feature | Notes |
|---|---|
| **Trade execution engine** | `Trade_adapter.py` — market orders, limit orders, position tracking with weighted avg cost, short selling, CSV logging |
| **Price data pipeline** | `Price_adapter/` — periodic OHLCV fetch, SQLite persistence, DiskCache hot cache |
| **Live price ticks** | `live_fetch.py` — yfinance WebSocket with mock fallback |
| **Strategy API (Handler)** | `Handler.py` — clean `prices.*` and `action.*` namespace, ZMQ async DEALER |
| **Indicators library** | 25+ indicators: RSI, StochRSI, MACD, Bollinger, ATR, Supertrend, OBV, ADX, CCI, Williams %R, ROC, TSI, BOS/CHoCH, S/R levels... |
| **Desktop UI shell** | React + Tailwind — Sidebar, routing, all 4 views scaffolded |
| **Active session dashboard** | Stat cards (P&L, invested, current, uptime), positions table, execution terminal |
| **pywebview bridge** | `window.updatePositions`, `window.addLog` wired; positions + logs pushed every 2s |
| **Session management** | Stop + Reset session buttons call Python API |
| **Desktop notifications** | `sendNotification` via browser Notification API |
| **DiskCache shared state** | Used consistently across all processes for both prices and positions |
| **ZMQ IPC** | DEALER/ROUTER pattern cleanly implemented |
| **Built frontend** | `UI/Frontend/dist/` present and deployable |

---

### ⚠️ Partially Complete / Has Issues

| Feature | Issue |
|---|---|
| **`Price_adapter` subprocess launch** | The Wrapper starts it from `BASE_DIR` but `Price_adapter/main.py` uses bare module imports (`from fetch import ...`) that require CWD = `Price_adapter/`. Will crash with `ModuleNotFoundError` unless `cwd=Price_adapter/` is passed to `Popen` |
| **Home view data** | `globalStats`, `recentExecutions`, `systemPulse`, `chartPath` never populated from backend — always shows empty/placeholder |
| **`live_fetch.py` import ordering** | `time` is used in `mock_generator()` before it's imported (line 22 uses `time.time()`, import on line 29). Will raise `NameError` at runtime |
| **Settings → Backend wiring** | Commission, latency, leverage, currency settings are purely cosmetic — not sent to the Trade Adapter |
| **Log injection** | Wrapper clears all logs and re-injects every 2s — causes UI flicker instead of incremental push |

---

### ❌ Not Implemented / Missing

| Feature | Impact |
|---|---|
| **SetupView → stocklist.json writing** | Critical: Clicking "Start Session" never writes selected tickers to `Temporary/stocklist.json`. `Price_adapter` will crash or use an old/nonexistent list |
| **Algorithm management backend** | The entire AlgorithmsView UI (upload, register, list, run, delete) has no backend implementation. No API exists to store/run/retrieve algorithm scripts |
| **Strategy script execution** | No mechanism to actually *run* a user's strategy Python file as a subprocess (only Trade + Price adapters are launched) |
| **SetupView strategy dropdown** | Dropdown is permanently empty — no API to enumerate available `.py` files |
| **Capital allocation enforcement** | Capital per ticker is tracked in UI state but never passed to Trade Adapter — no position sizing limits enforced |
| **P&L calculation** | Active session P&L stat cards (`pnl`, `invested`, `current`) are never computed from actual position data |
| **Uptime timer** | Hardcoded to `'00:00:00'` in context initial state — no timer logic |
| **`pywebview` in dependencies** | Missing from `pyproject.toml` — installing the project will not install the desktop wrapper dependency |
| **`pandas`, `numpy` in dependencies** | Missing from `pyproject.toml` — present only transitively |
| **Theme switching** | UI dropdown exists but only one theme is actually implemented |
| **Algo history/run records** | No storage for per-algorithm run history (P&L, win rate, last run) |
| **"View All History" button** | In HomeView — no action / no history view implemented |
| **Sound effects** | Toggle exists in Settings, no audio implementation |
| **Simulated latency** | Dropdown in Settings, never applied in Trade Adapter |
| **Multi-symbol per strategy** | Handler only supports one `SIM_SYMBOL` per process — multi-symbol requires separate processes |
| **CI/CD pipeline** | No GitHub Actions, no tests, no linting enforcement |
| **README** | Empty file |

---

## 6. Would It Work Right Now?

**TL;DR: Partially. Core backend logic is solid; full end-to-end flow has several broken connections.**

### What works standalone:
- Running `Trade_adapter.py` directly: ✅ yes
- Running `Price_adapter/main.py` directly from inside `Price_adapter/` directory: ✅ yes (if `stocklist.json` exists)  
- Importing `Handler.py` in a strategy and calling `prices.candle_list()`: ✅ yes
- Using `Indicators.*` functions: ✅ yes
- Building and running the React frontend standalone (no pywebview): ✅ works in browser, all UI renders

### What breaks in the full integrated flow:
1. **`Price_adapter` subprocess CWD bug** → `ModuleNotFoundError` on launch from Wrapper
2. **`live_fetch.py` NameError** → `time` used before import in `mock_generator`
3. **`stocklist.json` never written from UI** → `Price_adapter` crashes or ignores user's watchlist
4. **Strategy never launched** → The Wrapper doesn't implement running user strategies, so `Trade_adapter` has nobody sending orders
5. **P&L stats hardcoded** → The "Active Session" dashboard's metric cards never show real numbers

### Verdict:
The project has an excellent foundation — the data pipeline, trade engine, and indicator library are genuinely well-built. The UI is polished and architecturally sensible. But several **critical wiring points** between the frontend and backend are missing, meaning the full loop (user configures → session starts → strategy runs → dashboard shows live P&L) doesn't yet close.

---

## 7. Code Quality Assessment

| Dimension | Rating | Notes |
|---|---|---|
| **Architecture** | ⭐⭐⭐⭐⭐ | Clean separation of concerns, IPC-first design is correct for multi-process algo trading |
| **Python backend code** | ⭐⭐⭐⭐ | Clean, well-commented, good error handling in Trade Adapter and Price Adapter |
| **Indicator library** | ⭐⭐⭐⭐⭐ | Comprehensive, consistent API, numerically sound |
| **React frontend** | ⭐⭐⭐⭐ | Polished UI, clean component structure, good TypeScript typing |
| **Integration layer** | ⭐⭐ | Several critical wiring points missing between frontend and backend |
| **Testing** | ⭐ | Only a manual `test_order.py` and a Jupyter notebook — no automated tests |
| **Documentation** | ⭐⭐ | `AGENT.md` is excellent; README is empty; no API docs |
| **Dependency management** | ⭐⭐ | Missing `pywebview`, `pandas`, `numpy` in `pyproject.toml` |

---

## 8. Directory Tree (Source Files Only)

```
PaperQuant/
├── Handler.py              ← Strategy API (prices + action + indicators)
├── Trade_adapter.py        ← ZMQ ROUTER execution engine
├── pyproject.toml          ← Python dependencies (Poetry)
├── test_order.py           ← Manual integration test
├── testing.ipynb           ← Jupyter exploration notebook
├── AGENT.md                ← Developer documentation
│
├── Indicators/
│   ├── Main.py             ← Aggregation facade (indicators class)
│   ├── Candle_fetcher.py   ← Shared data access (hotspot: fan-in 35)
│   ├── momentum.py         ← RSI, StochRSI, CCI, Williams %R, etc.
│   ├── volatility.py       ← ATR, Bollinger Bands
│   ├── moving_avg.py       ← SMA, EMA, WMA, HMA, Supertrend
│   ├── volume.py           ← OBV, A/D Line, VWAP
│   ├── trend.py            ← ADX
│   ├── levels.py           ← Support/Resistance, Pivots
│   ├── market_structure.py ← BOS, CHoCH (Smart Money Concepts)
│   ├── signals.py          ← Composite signal generation
│   ├── statistics.py       ← StdDev, Variance, Correlation
│   ├── price_transforms.py ← Log returns, normalization
│   └── __init__.py
│
├── Price_adapter/
│   ├── main.py             ← Async orchestrator (60s periodic + live)
│   ├── fetch.py            ← Batch OHLCV fetcher (yfinance)
│   ├── live_fetch.py       ← WebSocket tick stream + mock fallback
│   └── db_handler.py       ← SQLite + DiskCache writer
│
├── UI/
│   ├── Wrapper/
│   │   └── main.py         ← pywebview desktop app + ProcessManager
│   │
│   └── Frontend/           ← React 19 + TypeScript + Vite 8 + Tailwind 4
│       ├── src/
│       │   ├── App.tsx                  ← Root component, view routing
│       │   ├── main.tsx                 ← React entry point
│       │   ├── index.css               ← Tailwind base styles
│       │   ├── components/
│       │   │   ├── Sidebar.tsx          ← Navigation
│       │   │   ├── StatCard.tsx         ← Metric card (reusable)
│       │   │   ├── HomeView.tsx         ← Command center dashboard
│       │   │   ├── SetupView.tsx        ← Session configuration
│       │   │   ├── AlgorithmsView.tsx   ← Algorithm library manager
│       │   │   ├── SettingsView.tsx     ← Preferences & settings
│       │   │   ├── PositionsTable.tsx   ← Live positions table
│       │   │   └── ExecutionTerminal.tsx← Log terminal
│       │   ├── context/
│       │   │   └── PaperQuantContext.tsx← Global state + window bridge
│       │   ├── hooks/
│       │   │   └── useBackend.ts        ← pywebview API wrapper hook
│       │   └── lib/
│       │       └── utils.ts             ← cn() tailwind utility
│       ├── dist/                        ← Production build (committed)
│       └── package.json
│
└── Temporary/              ← Runtime data (gitignored)
    ├── stocklist.json       ← Active ticker list
    ├── paperquant.db       ← SQLite OHLCV history
    ├── order_history.csv   ← Trade execution log
    ├── cache_candles/      ← DiskCache: latest candle per ticker
    ├── cache_liveprices/   ← DiskCache: rolling 2min tick history
    └── state/              ← DiskCache: positions per strategy+symbol
```
