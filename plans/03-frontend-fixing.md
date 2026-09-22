# Plan 3: Frontend Fixing & Wiring

> **Phase**: 3 of 4 (Runs in PARALLEL with Plan 2 after Plan 1 is finalized)  
> **Depends on**: Plan 1 (API Specification) — the single source of truth  
> **Estimated Effort**: ~10 hours  
> **Output**: A fully functional React frontend that communicates with the FastAPI backend via HTTP + WebSocket

---

## 1. Goal

Replace the `pywebview` bridge with standard HTTP/WebSocket communication, fix all data schema mismatches, wire up every "dead" UI component to real backend data, and prepare the frontend for Tauri packaging.

---

## 2. Current State — What's Broken

### 2.1 Critical Data Mismatches (Crashes)

| Component | Expects | Gets | Result |
|---|---|---|---|
| `PositionsTable.tsx` (L36) | `pos.pnl.startsWith('+')` | `pos.pnl` is `undefined` | **TypeError crash** |
| `ExecutionTerminal.tsx` (L29-30) | `log.time`, `log.content`, `log.color` | `log.id`, `log.message`, `log.timestamp`, `log.type` | **Blank terminal** |

### 2.2 Dead UI Slots (Never Populated)

| Component | Dead Data | Why |
|---|---|---|
| `HomeView.tsx` | `globalStats`, `recentExecutions`, `systemPulse`, `chartPath` | Backend never calls `window.updateGlobalStats` etc. |
| `SetupView.tsx` | Strategy dropdown always empty | No API to list strategies |
| `SetupView.tsx` | Watchlist never sent to backend | `onStart` doesn't pass data |
| `AlgorithmsView.tsx` | `algos` array always `[]` | No API, no setter `setAlgos` |
| `SettingsView.tsx` | All settings cosmetic | Never persisted to backend |
| Active session StatCards | P&L, Invested, Current, Uptime all `'-'` | Backend doesn't compute these |

### 2.3 Missing Click Handlers

| Component | Element | Missing |
|---|---|---|
| `AlgorithmsView.tsx` | "Register Algorithm" button | No `onClick` |
| `AlgorithmsView.tsx` | "Configure & Run" button | No `onClick` |
| `AlgorithmsView.tsx` | "Delete" button | No `onClick` |
| `ExecutionTerminal.tsx` | "Clear" button | No `onClick` (but `clearLogs` exists) |
| `HomeView.tsx` | "View All History" button | No `onClick` |
| `SettingsView.tsx` | "Check for updates" button | No `onClick` |
| `SettingsView.tsx` | Terminal font size buttons | No `onClick` |

### 2.4 Hardcoded/Fake Values

| Component | Value | Reality |
|---|---|---|
| `SettingsView.tsx` L214 | `"CONNECTED (12ms)"` | Not a real health check |
| `SettingsView.tsx` L220 | `"v1.0.0 (Production Build)"` | Static string |
| `ExecutionTerminal.tsx` L20 | `"Strategy_Engine_V1.0"` | Static |
| Active session green dot | Always `animate-pulse` | Not tied to real status |

---

## 3. Architectural Change: pywebview → HTTP/WebSocket

### 3.1 Remove pywebview Bridge

**Delete/Replace**:
- `window.pywebview.api.*` calls → HTTP `fetch()` calls
- `window.updatePositions()` / `window.addLog()` globals → WebSocket event handlers
- `useBackend.ts` hook → new `useApi.ts` hook with HTTP + WebSocket

### 3.2 New Communication Layer

```
React Frontend
     │
     ├── HTTP (fetch) ──→ GET/POST/PUT/DELETE /api/*
     │                     (commands, queries)
     │
     └── WebSocket ←──── ws://127.0.0.1:{PORT}/ws
                          (real-time events: positions, logs, stats, trades)
```

### 3.3 Port Discovery

The frontend needs to know which port the backend is running on. In the Tauri context:
1. Tauri spawns the Python sidecar
2. Python prints `PAPERQUANT_PORT=XXXXX` to stdout
3. Tauri captures this and passes it to the frontend via a Tauri command
4. For development: read from `~/.paperquant/port` or use env var `VITE_API_PORT`

---

## 4. New File Structure

```
UI/Frontend/src/
├── App.tsx                      ← [MODIFY] Update session flow, pass data to SetupView
├── main.tsx                     ← (no changes)
├── index.css                    ← (no changes)
├── types/
│   └── api.ts                   ← [NEW] All TypeScript interfaces from API spec
├── hooks/
│   ├── useBackend.ts            ← [DELETE] Replace with useApi.ts
│   ├── useApi.ts                ← [NEW] HTTP fetch wrapper with port discovery
│   └── useWebSocket.ts          ← [NEW] WebSocket connection + event handling
├── context/
│   └── PaperQuantContext.tsx    ← [MODIFY] Remove window.* globals, use WebSocket
├── lib/
│   ├── utils.ts                 ← (no changes)
│   └── api-client.ts            ← [NEW] Typed HTTP client for all endpoints
├── components/
│   ├── Sidebar.tsx              ← (no changes)
│   ├── StatCard.tsx             ← (no changes)
│   ├── HomeView.tsx             ← [MODIFY] Wire to real data via context
│   ├── SetupView.tsx            ← [MODIFY] Wire strategy dropdown, send data to backend
│   ├── AlgorithmsView.tsx       ← [MODIFY] Full CRUD wiring
│   ├── SettingsView.tsx         ← [MODIFY] Wire to backend settings API
│   ├── PositionsTable.tsx       ← [MODIFY] Use correct Position type
│   └── ExecutionTerminal.tsx    ← [MODIFY] Wire clear button, fix log shape
```

---

## 5. Detailed Implementation Tasks

### 5.1 Task 1: Create Shared TypeScript Types

**File: `src/types/api.ts`** [NEW]

```typescript
// ===== Shared API Types =====
// Single source of truth for frontend data shapes.
// Must match Plan 1 API spec exactly.

export interface Position {
  ticker: string;
  initials: string;
  qty: number;
  avg_price: number;
  current_price: number;
  invested: string;
  current: string;
  pnl: string;
  pnl_percent: string;
  strategy_id: string;
}

export interface LogEntry {
  time: string;
  content: string;
  color: string;
}

export interface RecentExecution {
  name: string;
  pnl: string;
  winRate: string;
  lastRun: string;
  status: 'profit' | 'loss';
}

export interface SystemPulseEntry {
  time: string;
  msg: string;
  color: string;
}

export interface GlobalStats {
  total_pnl: string;
  pnl_percent: string;
  active_algos: string;
  algo_runtime: string;
  pnl_trend: 'up' | 'down' | 'none';
}

export interface SessionStats {
  pnl: string;
  invested: string;
  current: string;
  uptime: string;
  trend: 'up' | 'down' | 'none';
}

export interface Algorithm {
  id: string;
  name: string;
  filename: string;
  dependencies: string[];
  created_at: string;
  history: AlgorithmRun[];
}

export interface AlgorithmRun {
  run_id: string;
  date: string;
  pnl: string;
  status: 'Completed' | 'Stopped' | 'Failed';
  duration_seconds: number;
}

export interface WatchlistItem {
  ticker: string;
  capital: number;
}

export interface Settings {
  currency: string;
  theme: string;
  simulated_latency_ms: number;
  commission_percent: number;
  leverage: number;
  auto_clear_logs: boolean;
  system_alerts: boolean;
  sound_effects: boolean;
  terminal_font_size: number;
}

export interface SessionStartRequest {
  watchlist: WatchlistItem[];
  strategy_id?: string;
  settings?: Partial<Settings>;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  adapters: {
    price_adapter: string;
    trade_adapter: string;
  };
}

// WebSocket event types
export type WSEventType =
  | 'positions_update'
  | 'log'
  | 'stats_update'
  | 'strategy_update'
  | 'system_pulse'
  | 'chart_update'
  | 'price_tick'
  | 'trade_executed'
  | 'adapter_status'
  | 'session_ended'
  | 'error';

export interface WSEvent<T = unknown> {
  type: WSEventType;
  data: T;
  timestamp: string;
}
```

---

### 5.2 Task 2: Create API Client

**File: `src/lib/api-client.ts`** [NEW]

```typescript
import type {
  Position, Algorithm, Settings, SessionStartRequest,
  HealthResponse, LogEntry, SessionStats, GlobalStats,
} from '../types/api';

class ApiClient {
  private baseUrl: string;

  constructor() {
    // Port discovery: Tauri will inject this, or use env var for dev
    const port = (window as any).__PAPERQUANT_PORT__
      || import.meta.env.VITE_API_PORT
      || '8000';
    this.baseUrl = `http://127.0.0.1:${port}`;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `API error: ${response.status}`);
    }
    return response.json();
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.request('/api/health');
  }

  // Session
  async startSession(config: SessionStartRequest): Promise<{ status: string; session_id: string }> {
    return this.request('/api/session/start', { method: 'POST', body: JSON.stringify(config) });
  }

  async stopSession(): Promise<{ status: string; session_id: string; duration_seconds: number }> {
    return this.request('/api/session/stop', { method: 'POST' });
  }

  async resetSession(): Promise<{ status: string }> {
    return this.request('/api/session/reset', { method: 'POST' });
  }

  async getSessionStatus(): Promise<any> {
    return this.request('/api/session/status');
  }

  // Positions
  async getPositions(): Promise<{ positions: Position[] }> {
    return this.request('/api/positions');
  }

  async getTradeHistory(): Promise<{ trades: any[] }> {
    return this.request('/api/positions/history');
  }

  // Stats
  async getStats(): Promise<{ session: SessionStats; global: GlobalStats }> {
    return this.request('/api/stats');
  }

  async getChartData(): Promise<{ timestamps: string[]; pnl_values: number[] }> {
    return this.request('/api/stats/chart');
  }

  // Algorithms
  async getAlgorithms(): Promise<{ algorithms: Algorithm[] }> {
    return this.request('/api/algorithms');
  }

  async uploadAlgorithm(file: File, name: string, dependencies: string): Promise<Algorithm> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('dependencies', dependencies);
    
    const response = await fetch(`${this.baseUrl}/api/algorithms`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }

  async deleteAlgorithm(id: string): Promise<void> {
    await this.request(`/api/algorithms/${id}`, { method: 'DELETE' });
  }

  async runAlgorithm(id: string, symbol: string): Promise<any> {
    return this.request(`/api/algorithms/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    });
  }

  async stopAlgorithm(id: string): Promise<any> {
    return this.request(`/api/algorithms/${id}/stop`, { method: 'POST' });
  }

  // Settings
  async getSettings(): Promise<Settings> {
    return this.request<{ settings: Settings }>('/api/settings').then(r => r.settings || r as any);
  }

  async updateSettings(updates: Partial<Settings>): Promise<Settings> {
    return this.request<{ settings: Settings }>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(updates),
    }).then(r => r.settings || r as any);
  }

  // Logs
  async getLogs(limit: number = 100): Promise<{ logs: LogEntry[] }> {
    return this.request(`/api/logs?limit=${limit}`);
  }

  // Market
  async getMarketPrices(): Promise<{ prices: Record<string, { price: number; timestamp: string }> }> {
    return this.request('/api/market/prices');
  }

  // WebSocket URL
  getWebSocketUrl(): string {
    const port = (window as any).__PAPERQUANT_PORT__
      || import.meta.env.VITE_API_PORT
      || '8000';
    return `ws://127.0.0.1:${port}/ws`;
  }
}

export const apiClient = new ApiClient();
```

---

### 5.3 Task 3: Create WebSocket Hook

**File: `src/hooks/useWebSocket.ts`** [NEW]

```typescript
import { useEffect, useRef, useCallback, useState } from 'react';
import { apiClient } from '../lib/api-client';
import type { WSEvent, WSEventType } from '../types/api';

type EventHandler = (data: any) => void;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const handlersRef = useRef<Map<WSEventType, EventHandler[]>>(new Map());
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    const url = apiClient.getWebSocketUrl();
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('[WS] Connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const msg: WSEvent = JSON.parse(event.data);
        const handlers = handlersRef.current.get(msg.type);
        if (handlers) {
          handlers.forEach(handler => handler(msg.data));
        }
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };
    
    ws.onerror = () => {
      ws.close();
    };
    
    wsRef.current = ws;
  }, []);

  const on = useCallback((type: WSEventType, handler: EventHandler) => {
    const existing = handlersRef.current.get(type) || [];
    handlersRef.current.set(type, [...existing, handler]);
    
    return () => {
      const current = handlersRef.current.get(type) || [];
      handlersRef.current.set(type, current.filter(h => h !== handler));
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected, on };
}
```

---

### 5.4 Task 4: Rewrite PaperQuantContext

**File: `src/context/PaperQuantContext.tsx`** [MODIFY — Major Rewrite]

The context should no longer expose `window.*` globals. Instead, it consumes WebSocket events and provides state to all children.

Key changes:
- Remove all `window.*` global registrations
- Add WebSocket event handlers that update state
- Import types from `types/api.ts`
- Load initial data via HTTP on mount

```typescript
// Simplified structure (key changes):

import { useWebSocket } from '../hooks/useWebSocket';
import { apiClient } from '../lib/api-client';
import type { Position, LogEntry, GlobalStats, SessionStats, /* ... */ } from '../types/api';

export function PaperQuantProvider({ children }: { children: ReactNode }) {
  const { isConnected, on } = useWebSocket();
  
  // State (same variables, new types from api.ts)
  const [positions, setPositions] = useState<Position[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<SessionStats>({ pnl: '-', invested: '-', current: '-', uptime: '00:00:00', trend: 'none' });
  const [globalStats, setGlobalStats] = useState<GlobalStats>({ total_pnl: '$0.00', pnl_percent: '0%', active_algos: '0', algo_runtime: '0h', pnl_trend: 'none' });
  // ... other state ...

  // Register WebSocket handlers
  useEffect(() => {
    const unsubs = [
      on('positions_update', (data) => setPositions(data.positions)),
      on('log', (data) => setLogs(prev => [...prev.slice(-99), data])),
      on('stats_update', (data) => {
        setStats(data.session);
        setGlobalStats(data.global);
      }),
      on('system_pulse', (data) => setSystemPulse(prev => [data, ...prev.slice(0, 19)])),
      on('strategy_update', (data) => setStrategyName(data.name)),
      on('chart_update', (data) => { /* Update chart data */ }),
      on('trade_executed', (data) => {
        sendNotification(`Trade Executed: ${data.side} ${data.qty} ${data.symbol}`, `Price: $${data.price}`);
      }),
    ];
    return () => unsubs.forEach(unsub => unsub());
  }, [on]);

  // NO MORE window.* globals!
  // ...
}
```

---

### 5.5 Task 5: Rewrite SetupView

**File: `src/components/SetupView.tsx`** [MODIFY]

Key changes:
- Fetch algorithms list on mount → populate strategy dropdown
- Pass watchlist + strategy_id to backend on "Start Session"
- Accept `onStart` with data payload

```typescript
// Key changes:
interface SetupViewProps {
  onStart: (config: SessionStartRequest) => void;
}

export function SetupView({ onStart }: SetupViewProps) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  
  // Fetch algorithms on mount
  useEffect(() => {
    apiClient.getAlgorithms().then(res => setAlgorithms(res.algorithms)).catch(console.error);
  }, []);
  
  const handleStart = () => {
    onStart({
      watchlist: watchlist.map(w => ({ ticker: w.ticker, capital: parseFloat(w.capital) })),
      strategy_id: selectedStrategy || undefined,
    });
  };
  
  // Strategy dropdown now populated:
  <select value={selectedStrategy} onChange={e => setSelectedStrategy(e.target.value)}>
    <option value="">Manual Trading (No Strategy)</option>
    {algorithms.map(algo => (
      <option key={algo.id} value={algo.id}>{algo.name}</option>
    ))}
  </select>
}
```

---

### 5.6 Task 6: Rewrite AlgorithmsView

**File: `src/components/AlgorithmsView.tsx`** [MODIFY]

Key changes:
- Add `setAlgos` setter (currently missing!)
- Fetch algorithms on mount
- Wire "Register Algorithm" to `POST /api/algorithms`
- Wire "Delete" to `DELETE /api/algorithms/{id}`
- Wire "Configure & Run" to `POST /api/algorithms/{id}/run`

```typescript
// Key changes:
const [algos, setAlgos] = useState<Algorithm[]>([]);  // ADD SETTER

// Fetch on mount
useEffect(() => {
  apiClient.getAlgorithms()
    .then(res => setAlgos(res.algorithms))
    .catch(console.error);
}, []);

// Register algorithm
const handleRegister = async () => {
  if (!pendingFile || !algoName) return;
  try {
    const newAlgo = await apiClient.uploadAlgorithm(pendingFile, algoName, depsInput);
    setAlgos(prev => [...prev, newAlgo]);
    resetForm();
  } catch (e) {
    console.error('Registration failed:', e);
  }
};

// Delete algorithm
const handleDelete = async (algoId: string) => {
  try {
    await apiClient.deleteAlgorithm(algoId);
    setAlgos(prev => prev.filter(a => a.id !== algoId));
  } catch (e) {
    console.error('Delete failed:', e);
  }
};

// Run algorithm
const handleRun = async (algoId: string) => {
  try {
    await apiClient.runAlgorithm(algoId, 'AAPL'); // TODO: symbol picker
  } catch (e) {
    console.error('Run failed:', e);
  }
};
```

---

### 5.7 Task 7: Rewrite SettingsView

**File: `src/components/SettingsView.tsx`** [MODIFY]

Key changes:
- Fetch settings on mount from `GET /api/settings`
- Wire all dropdowns/toggles to `PUT /api/settings`
- Replace hardcoded Python Engine status with real health check
- Wire font size buttons

```typescript
// Key changes:
const [settings, setSettings] = useState<Settings | null>(null);
const [health, setHealth] = useState<HealthResponse | null>(null);

useEffect(() => {
  apiClient.getSettings().then(setSettings).catch(console.error);
  apiClient.getHealth().then(setHealth).catch(console.error);
}, []);

const updateSetting = async (key: string, value: any) => {
  const updated = await apiClient.updateSettings({ [key]: value });
  setSettings(updated);
};

// Python Engine Status (replaces hardcoded "CONNECTED (12ms)"):
<span className={health ? 'text-green-400' : 'text-red-400'}>
  {health ? `CONNECTED (v${health.version})` : 'DISCONNECTED'}
</span>

// Version display:
<span>{health?.version ? `v${health.version}` : 'Unknown'}</span>
```

---

### 5.8 Task 8: Fix PositionsTable

**File: `src/components/PositionsTable.tsx`** [MODIFY]

The Position type from the new API now includes all required fields (`pnl`, `invested`, `current`, `initials`, `ticker`), so the component should work correctly after the type imports are updated. Only minor safety fixes needed:

```typescript
// Add safe check for pnl formatting:
const isProfitable = pos.pnl?.startsWith('+') ?? false;
```

---

### 5.9 Task 9: Fix ExecutionTerminal

**File: `src/components/ExecutionTerminal.tsx`** [MODIFY]

- Wire "Clear" button to `setLogs([])` from context
- Log entries now have correct shape from WebSocket

```typescript
// Wire clear button:
const { logs, setLogs } = usePaperQuant();

<button onClick={() => setLogs([])}>Clear</button>

// Logs are now correctly shaped as {time, content, color} from WebSocket
```

---

### 5.10 Task 10: Update App.tsx

**File: `src/App.tsx`** [MODIFY]

Key changes:
- Replace `useBackend` hook with API client
- Pass session config from SetupView to backend
- Handle session start/stop via HTTP calls

```typescript
// Replace:
const { isReady, callBackend } = useBackend();

// With:
import { apiClient } from './lib/api-client';

const handleStartSession = async (config: SessionStartRequest) => {
  try {
    await apiClient.startSession(config);
    setView('active');
  } catch (e) {
    console.error('Failed to start session:', e);
  }
};

const handleStopSession = async () => {
  try {
    await apiClient.stopSession();
    setView('setup');
  } catch (e) {
    console.error('Failed to stop session:', e);
  }
};

const handleResetSession = async () => {
  try {
    await apiClient.resetSession();
  } catch (e) {
    console.error('Failed to reset session:', e);
  }
};
```

---

### 5.11 Task 11: Delete useBackend.ts

**File: `src/hooks/useBackend.ts`** [DELETE]

This file is entirely replaced by `useApi.ts` (API client) and `useWebSocket.ts` (event streaming). All consumers must be updated.

---

### 5.12 Task 12: Update HomeView

**File: `src/components/HomeView.tsx`** [MODIFY]

Key changes:
- Context now provides real `globalStats`, `recentExecutions`, `systemPulse` via WebSocket
- The SVG chart should be generated from `chartData` (P&L time series)
- Wire "View All History" button to navigate to a history view (or show modal)

```typescript
// Chart rendering from P&L data:
const generateChartPath = (pnlValues: number[]): string => {
  if (pnlValues.length < 2) return '';
  const maxVal = Math.max(...pnlValues.map(Math.abs), 1);
  const points = pnlValues.map((v, i) => {
    const x = (i / (pnlValues.length - 1)) * 100;
    const y = 20 - (v / maxVal) * 18;  // Center at y=20, scale ±18
    return `${x},${y}`;
  });
  return `M ${points.join(' L ')}`;
};
```

---

## 6. Development & Build Configuration Changes

### 6.1 Vite Dev Config

For local development without Tauri, set the API port:

```bash
# .env.development
VITE_API_PORT=8000
```

### 6.2 package.json Updates

Add new dependencies if needed (none should be necessary — all communication uses native `fetch` and `WebSocket`).

Remove unused imports across all files:
- `Wallet` from `SetupView.tsx`
- `TrendingUp`, `Building2`, `Tag` from `SettingsView.tsx`

### 6.3 Build Verification

```bash
cd UI/Frontend
npm run build    # tsc -b && vite build
npm run lint     # eslint .
```

---

## 7. Verification Plan

### Automated Tests
```bash
cd UI/Frontend

# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Build (ensures no dead imports, missing types)
npm run build

# Playwright E2E tests (if configured)
npx playwright test
```

### Manual Verification

1. **Start backend**: `python api_server.py` (from Plan 2)
2. **Start frontend dev**: `cd UI/Frontend && npm run dev`
3. **Verify each view**:

| View | Test Steps | Expected |
|---|---|---|
| Home | Open app | StatCards show real data, chart renders, system pulse shows events |
| Setup | Add tickers, select strategy, click Start | Session starts, navigates to Active view |
| Active | Observe during session | Positions table shows enriched data with P&L, terminal shows colored logs, stat cards update every 2s |
| Algorithms | Upload a `.py` file | File registered, appears in list |
| Algorithms | Click Delete | Algorithm removed |
| Algorithms | Click Run | Strategy subprocess starts |
| Settings | Change commission | Value persists after page refresh |
| Settings | Check engine status | Shows real connection status |

### CI/CD Quality Gates
```bash
# Phase 1: Code Quality
cd UI/Frontend
npx tsc --noEmit
npm run lint

# Phase 2: Build
npm run build
```

---

## 8. Migration Checklist

- [ ] Create `src/types/api.ts` with all shared types
- [ ] Create `src/lib/api-client.ts` with typed HTTP client
- [ ] Create `src/hooks/useWebSocket.ts` with WS connection management
- [ ] Rewrite `PaperQuantContext.tsx` — remove `window.*` globals, use WebSocket
- [ ] Delete `src/hooks/useBackend.ts`
- [ ] Update `App.tsx` — use API client, pass config to SetupView
- [ ] Update `SetupView.tsx` — populate strategy dropdown, send config to backend
- [ ] Update `AlgorithmsView.tsx` — add setter, wire CRUD operations
- [ ] Update `SettingsView.tsx` — fetch/persist settings, real health check
- [ ] Fix `PositionsTable.tsx` — safe `pnl` check
- [ ] Fix `ExecutionTerminal.tsx` — wire clear button
- [ ] Update `HomeView.tsx` — generate SVG chart from data
- [ ] Remove unused imports across all files
- [ ] Run `tsc --noEmit` to verify types
- [ ] Run `npm run build` to verify build
- [ ] Rebuild `dist/` for Tauri packaging
