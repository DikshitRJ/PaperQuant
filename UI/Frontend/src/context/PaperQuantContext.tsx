import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface Position {
  ticker: string;
  pnl: string;
  invested: string;
  current: string;
  initials: string;
}

interface LogEntry {
  time: string;
  content: string;
  color: string;
}

interface RecentExecution {
  name: string;
  pnl: string;
  winRate: string;
  lastRun: string;
  status: 'profit' | 'loss';
}

interface SystemPulseEntry {
  time: string;
  msg: string;
  color: string;
}

interface GlobalStats {
  totalPnl: string;
  pnlPercent: string;
  activeAlgos: string;
  algoRuntime: string;
  pnlTrend: 'up' | 'down' | 'none';
}

interface PaperQuantContextType {
  // Active Session state
  positions: Position[];
  logs: LogEntry[];
  stats: {
    pnl: string;
    invested: string;
    current: string;
    uptime: string;
    trend: 'up' | 'down' | 'none';
  };
  strategyName: string;
  
  // Home (Command Center) state
  globalStats: GlobalStats;
  recentExecutions: RecentExecution[];
  systemPulse: SystemPulseEntry[];
  chartPath: string; // The "d" attribute for the SVG path
  
  // Setters
  setPositions: (p: Position[]) => void;
  addLog: (log: LogEntry) => void;
  setStats: (stats: PaperQuantContextType['stats']) => void;
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
  // Active Session state
  const [positions, setPositions] = useState<Position[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [strategyName, setStrategyName] = useState('-');
  const [stats, setStats] = useState<PaperQuantContextType['stats']>({
    pnl: '-',
    invested: '-',
    current: '-',
    uptime: '00:00:00',
    trend: 'none'
  });

  // Home state
  const [globalStats, setGlobalStats] = useState<GlobalStats>({
    totalPnl: '$0.00',
    pnlPercent: '0%',
    activeAlgos: '0',
    algoRuntime: '0h',
    pnlTrend: 'none'
  });
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([]);
  const [systemPulse, setSystemPulse] = useState<SystemPulseEntry[]>([]);
  const [chartPath, setChartPath] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const addLog = (log: LogEntry) => {
    setLogs(prev => [...prev.slice(-100), log]);
  };

  const addSystemPulse = (entry: SystemPulseEntry) => {
    setSystemPulse(prev => [entry, ...prev.slice(0, 19)]);
  };

  const sendNotification = (title: string, body: string) => {
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
  };

  // Optimization for pywebview: Expose these to global window
  useEffect(() => {
    (window as any).updatePositions = setPositions;
    (window as any).addLog = addLog;
    (window as any).updateStats = setStats;
    (window as any).updateStrategyName = setStrategyName;
    (window as any).clearLogs = () => setLogs([]);
    (window as any).sendNotification = sendNotification;
    (window as any).setNotificationsEnabled = setNotificationsEnabled;

    (window as any).updateGlobalStats = setGlobalStats;
    (window as any).updateRecentExecutions = setRecentExecutions;
    (window as any).addSystemPulse = addSystemPulse;
    (window as any).updateChartPath = setChartPath;

    return () => {
      const globals = [
        'updatePositions', 'addLog', 'updateStats', 'updateStrategyName', 
        'clearLogs', 'sendNotification', 'setNotificationsEnabled',
        'updateGlobalStats', 'updateRecentExecutions', 'addSystemPulse', 'updateChartPath'
      ];
      globals.forEach(g => delete (window as any)[g]);
    };
  }, [notificationsEnabled]); // Re-bind when enabled state changes to ensure closure has latest state

  return (
    <PaperQuantContext.Provider value={{ 
      positions, logs, stats, strategyName,
      globalStats, recentExecutions, systemPulse, chartPath,
      setPositions, addLog, setStats, setStrategyName,
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
