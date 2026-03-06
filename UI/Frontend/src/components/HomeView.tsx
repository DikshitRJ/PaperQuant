import React from 'react';
import { 
  TrendingUp, 
  Activity, 
  Clock, 
  ArrowUpRight, 
  Play,
  LayoutDashboard,
  History
} from 'lucide-react';
import { StatCard } from './StatCard';
import { cn } from '../lib/utils';
import { usePaperQuant } from '../context/PaperQuantContext';

interface RecentAlgoProps {
  name: string;
  pnl: string;
  winRate: string;
  lastRun: string;
  status: 'profit' | 'loss';
}

const RecentAlgoCard = ({ name, pnl, winRate, lastRun, status }: RecentAlgoProps) => (
  <div className="bg-[#262626]/40 border border-neutral-500/20 rounded-xl p-4 hover:border-white/20 transition-all group cursor-pointer">
    <div className="flex justify-between items-start mb-4">
      <div className="size-10 bg-white/5 rounded-lg flex items-center justify-center group-hover:bg-white/10 transition-colors">
        <Activity size={20} className="text-neutral-400" />
      </div>
      <div className={cn(
        "px-2 py-1 rounded text-xs font-bold font-mono uppercase tracking-tighter",
        status === 'profit' ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
      )}>
        {status === 'profit' ? "+" : ""}{pnl}
      </div>
    </div>
    <h3 className="text-white font-bold mb-1 truncate">{name}</h3>
    <div className="flex items-center gap-4 text-[10px] text-neutral-500 font-medium uppercase tracking-wider">
      <span>WR: <span className="text-neutral-300 font-mono">{winRate}</span></span>
      <span>{lastRun}</span>
    </div>
  </div>
);

const HomeView = () => {
  const { globalStats, recentExecutions, systemPulse, chartPath } = usePaperQuant();

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in duration-700">
      <header className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <LayoutDashboard size={18} className="text-neutral-500" />
          <span className="text-neutral-500 font-mono text-sm uppercase tracking-[0.2em]">Command Center</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-bold text-white tracking-tight">System Overview</h1>
      </header>

      {/* Top Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard 
          label="Total P&L" 
          value={globalStats.totalPnl} 
          subValue={globalStats.pnlPercent} 
          icon={TrendingUp} 
          trend={globalStats.pnlTrend !== 'none' ? globalStats.pnlTrend : undefined} 
        />
        <StatCard 
          label="Active Algos" 
          value={globalStats.activeAlgos} 
          subValue="Standby" 
          icon={Play} 
        />
        <StatCard 
          label="Algo Runtime" 
          value={globalStats.algoRuntime} 
          subValue="Total Session Time" 
          icon={Clock} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Main Chart */}
        <div className="lg:col-span-2 bg-[#171717]/40 border border-neutral-500/40 rounded-2xl p-6 relative overflow-hidden flex flex-col min-h-[400px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-white font-bold text-lg">Performance Pulse</h2>
              <p className="text-neutral-500 text-sm">Aggregated P&L over the session</p>
            </div>
          </div>
          
          <div className="flex-1 flex items-center justify-center mt-4 relative">
            {/* Zero Line */}
            <div className="absolute top-1/2 left-0 w-full h-px bg-white/10 z-0" />
            
            <svg className="w-full h-full min-h-[200px] z-10" viewBox="0 0 100 40" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chartGradientUp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(34, 197, 94, 0.3)" />
                  <stop offset="100%" stopColor="rgba(34, 197, 94, 0)" />
                </linearGradient>
                <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#ef4444" />
                  <stop offset="30%" stopColor="#ef4444" />
                  <stop offset="50%" stopColor="#22c55e" />
                  <stop offset="100%" stopColor="#22c55e" />
                </linearGradient>
              </defs>
              
              {/* Fill Area */}
              {chartPath && (
                <path 
                  d={`${chartPath} L100,20 L0,20 Z`} 
                  fill="url(#chartGradientUp)"
                  className="opacity-50"
                />
              )}
              
              {/* P&L Line */}
              {chartPath && (
                <path 
                  d={chartPath} 
                  fill="none" 
                  stroke="url(#lineGradient)" 
                  strokeWidth="1.5" 
                  vectorEffect="non-scaling-stroke"
                  strokeLinecap="round"
                />
              )}
            </svg>
            
            {/* Time Labels */}
            <div className="absolute bottom-0 left-0 w-full flex justify-between px-2 text-[8px] font-mono text-neutral-600 uppercase tracking-widest">
              <span>09:30</span>
              <span>12:00</span>
              <span>15:00</span>
              <span>16:00</span>
            </div>
          </div>

          <div className="absolute top-24 right-8 flex flex-col items-end">
             <div className={cn(
               "font-mono text-2xl font-bold flex items-center gap-1 animate-pulse",
               globalStats.pnlTrend === 'up' ? "text-green-500" : globalStats.pnlTrend === 'down' ? "text-red-500" : "text-neutral-400"
             )}>
               <ArrowUpRight size={24} className={globalStats.pnlTrend === 'down' ? "rotate-90" : ""} />
               {globalStats.totalPnl}
             </div>
             <span className="text-neutral-600 text-[10px] font-bold uppercase tracking-widest">Global P&L</span>
          </div>
        </div>

        {/* System Pulse (Health / Logs) */}
        <div className="bg-[#171717]/40 border border-neutral-500/40 rounded-2xl p-6 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <History size={18} className="text-neutral-400" />
            <h2 className="text-white font-bold">System Pulse</h2>
          </div>
          <div className="space-y-4 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10">
            {systemPulse.length > 0 ? (
              systemPulse.map((log, i) => (
                <div key={i} className="flex gap-3 text-xs border-l border-neutral-800 pl-3 py-1">
                  <span className="text-neutral-600 font-mono shrink-0">{log.time}</span>
                  <span className={cn("font-medium", log.color)}>{log.msg}</span>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-neutral-600 text-xs italic">
                Waiting for system heartbeat...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Strategies */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-neutral-400" />
            <h2 className="text-white font-bold">Recent Executions</h2>
          </div>
          <button className="text-neutral-500 hover:text-white text-xs font-bold uppercase transition-colors">View All History</button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recentExecutions.length > 0 ? (
            recentExecutions.map((algo, i) => (
              <RecentAlgoCard key={i} {...algo} />
            ))
          ) : (
            <div className="col-span-full py-12 bg-[#171717]/20 border border-dashed border-neutral-800 rounded-xl flex flex-col items-center justify-center gap-2 text-neutral-600">
               <Play size={24} className="opacity-20" />
               <span className="text-sm font-medium italic">No recent executions found.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default HomeView;
