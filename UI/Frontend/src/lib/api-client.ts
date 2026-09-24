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

/**
 * Wait for the backend sidecar to start and become healthy.
 * Polls window.__PAPERQUANT_PORT__ and /api/health every 500ms.
 * Used as a startup gate when running inside Tauri.
 */
export async function waitForBackend(timeoutMs: number = 30000): Promise<void> {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      const port = (window as any).__PAPERQUANT_PORT__
        || import.meta.env.VITE_API_PORT;
      if (port) {
        const response = await fetch(`http://127.0.0.1:${port}/api/health`);
        if (response.ok) return;
      }
    } catch {
      // Not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  throw new Error('Backend did not start within timeout');
}
