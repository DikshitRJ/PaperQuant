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
