import React, { useState } from 'react';
import { RotateCcw, Octagon, TrendingUp, Wallet, Activity, Clock } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { StatCard } from './components/StatCard';
import { PositionsTable } from './components/PositionsTable';
import { ExecutionTerminal } from './components/ExecutionTerminal';
import SetupView from './components/SetupView';
import HomeView from './components/HomeView';
import AlgorithmsView from './components/AlgorithmsView';
import SettingsView from './components/SettingsView';
import { useBackend } from './hooks/useBackend';
import { usePaperQuant } from './context/PaperQuantContext';

function App() {
  const [view, setView] = useState('home'); 
  const { isReady, callBackend } = useBackend();
  const { strategyName, stats } = usePaperQuant();

  const handleStartSession = () => {
    setView('active');
  };

  const handleStopSession = async () => {
    await callBackend(api => api.stop_session());
    setView('setup');
  };

  const handleResetSession = async () => {
    await callBackend(api => api.reset_session());
  };

  return (
    <div className="flex h-screen bg-black w-screen overflow-hidden text-slate-200 selection:bg-white/20 relative">
      {/* Subtle Background Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#1a1a1a_0%,_#000000_100%)] pointer-events-none" />
      
      <Sidebar currentView={view} setView={setView} />
      
      <main className="flex-1 overflow-y-auto relative scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent pb-20 md:pb-0">
        {view === 'home' ? (
          <HomeView />
        ) : view === 'setup' ? (
          <SetupView onStart={handleStartSession} />
        ) : view === 'algorithms' ? (
          <AlgorithmsView />
        ) : view === 'settings' ? (
          <SettingsView />
        ) : view === 'active' ? (
          <div className="max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl md:text-4xl font-bold text-white mb-2 tracking-tight">Active Session</h1>
                <div className="text-neutral-400 text-xs md:text-sm flex items-center gap-2 font-medium">
                  <div className="size-2 bg-green-500 rounded-full animate-pulse shrink-0" />
                  Running strategy: <span className="text-neutral-200">{strategyName}</span>
                </div>
              </div>
              <div className="flex gap-2 md:gap-3">
                <button 
                  onClick={handleResetSession}
                  className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-[#171717]/40 border border-neutral-500/40 rounded-lg px-4 md:px-5 py-2 md:py-2.5 text-neutral-200 hover:bg-white/5 hover:border-neutral-400 transition-all active:scale-95 text-sm md:text-base"
                >
                  <RotateCcw size={16} />
                  <span className="font-semibold">Reset</span>
                </button>
                <button 
                  onClick={handleStopSession}
                  className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-red-600 rounded-lg px-4 md:px-5 py-2 md:py-2.5 text-white hover:bg-red-700 transition-all shadow-lg shadow-red-600/20 active:scale-95 text-sm md:text-base"
                >
                  <Octagon size={16} />
                  <span className="font-semibold truncate">Stop Session</span>
                </button>
              </div>
            </header>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              <StatCard 
                label="Net P&L" 
                value={stats.pnl} 
                icon={TrendingUp} 
                trend={stats.trend !== 'none' ? stats.trend : undefined}
              />
              <StatCard 
                label="Invested Value" 
                value={stats.invested} 
                icon={Wallet} 
              />
              <StatCard 
                label="Current Value" 
                value={stats.current} 
                icon={Activity} 
              />
              <StatCard 
                label="Uptime" 
                value={stats.uptime} 
                icon={Clock} 
              />
            </div>

            <PositionsTable />
            <ExecutionTerminal />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-neutral-500 font-mono italic">
            View "{view}" is under construction...
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
