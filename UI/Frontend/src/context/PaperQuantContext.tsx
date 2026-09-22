import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import type { 
  Position, 
  LogEntry, 
  GlobalStats, 
  SessionStats, 
  RecentExecution, 
  SystemPulseEntry 
} from '../types/api';

interface PaperQuantContextType {
  // Active Session state
  positions: Position[];
  logs: LogEntry[];
  stats: SessionStats;
  strategyName: string;
  
  // Home (Command Center) state
  globalStats: GlobalStats;
  recentExecutions: RecentExecution[];
  systemPulse: SystemPulseEntry[];
  chartPath: string;
  
  // Setters
  setPositions: (p: Position[]) => void;
  setLogs: (logs: LogEntry[] | ((prev: LogEntry[]) => LogEntry[])) => void;
  addLog: (log: LogEntry) => void;
  setStats: (stats: SessionStats) => void;
  setStrategyName: (name: string) => void;
  
  setGlobalStats: (s: GlobalStats) => void;
  setRecentExecutions: (e: RecentExecution[]) => void;
  addSystemPulse: (p: SystemPulseEntry) => void;
  setChartPath: (path: string) => void;
  
  // Notification Handler
  sendNotification: (title: string, body: string) => void;
}

const PaperQuantContext = createContext<PaperQuantContextType | undefined>(undefined);

export const PaperQuantProvider = ({ children }: { children: ReactNode }) => {
  const { isConnected, on } = useWebSocket();

  // Active Session state
  const [positions, setPositions] = useState<Position[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [strategyName, setStrategyName] = useState('-');
  const [stats, setStats] = useState<SessionStats>({
    pnl: '-',
    invested: '-',
    current: '-',
    uptime: '00:00:00',
    trend: 'none'
  });

  // Home state
  const [globalStats, setGlobalStats] = useState<GlobalStats>({
    total_pnl: '$0.00',
    pnl_percent: '0%',
    active_algos: '0',
    algo_runtime: '0h',
    pnl_trend: 'none'
  });
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([]);
  const [systemPulse, setSystemPulse] = useState<SystemPulseEntry[]>([]);
  const [chartPath, setChartPath] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const addLog = useCallback((log: LogEntry) => {
    setLogs(prev => [...prev.slice(-99), log]);
  }, []);

  const addSystemPulse = useCallback((entry: SystemPulseEntry) => {
    setSystemPulse(prev => [entry, ...prev.slice(0, 19)]);
  }, []);

  const sendNotification = useCallback((title: string, body: string) => {
    if (!notificationsEnabled) return;
    
    if (!("Notification" in window)) {
      console.warn("Desktop notifications not supported");
      return;
    }

    if (Notification.permission === "granted") {
      new Notification(title, { body, icon: '/vite.svg' });
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then(permission => {
        if (permission === "granted") {
          new Notification(title, { body, icon: '/vite.svg' });
        }
      });
    }
  }, [notificationsEnabled]);

  // Register WebSocket handlers
  useEffect(() => {
    const unsubs = [
      on('positions_update', (data: any) => setPositions(data.positions || [])),
      on('log', (data: any) => addLog(data)),
      on('stats_update', (data: any) => {
        if (data.session) setStats(data.session);
        if (data.global) setGlobalStats(data.global);
      }),
      on('system_pulse', (data: any) => addSystemPulse(data)),
      on('strategy_update', (data: any) => setStrategyName(data.name || '-')),
      on('chart_update', (data: any) => {
        // Assume data contains { timestamps, pnl_values }
        if (data.pnl_values && Array.isArray(data.pnl_values)) {
          const pnlValues = data.pnl_values;
          if (pnlValues.length < 2) {
            setChartPath('');
          } else {
            const maxVal = Math.max(...pnlValues.map(Math.abs), 1);
            const points = pnlValues.map((v: number, i: number) => {
              const x = (i / (pnlValues.length - 1)) * 100;
              const y = 20 - (v / maxVal) * 18;  // Center at y=20, scale ±18
              return `${x},${y}`;
            });
            setChartPath(`M ${points.join(' L ')}`);
          }
        }
      }),
      on('trade_executed', (data: any) => {
        sendNotification(`Trade Executed: ${data.side} ${data.qty} ${data.symbol}`, `Price: $${data.price}`);
      }),
    ];
    return () => unsubs.forEach(unsub => unsub());
  }, [on, addLog, addSystemPulse, sendNotification]);

  return (
    <PaperQuantContext.Provider value={{ 
      positions, logs, stats, strategyName,
      globalStats, recentExecutions, systemPulse, chartPath,
      setPositions, setLogs, addLog, setStats, setStrategyName,
      setGlobalStats, setRecentExecutions, addSystemPulse, setChartPath,
      sendNotification
    }}>
      {children}
    </PaperQuantContext.Provider>
  );
};

export const usePaperQuant = () => {
  const context = useContext(PaperQuantContext);
  if (!context) throw new Error('usePaperQuant must be used within a PaperQuantProvider');
  return context;
};
