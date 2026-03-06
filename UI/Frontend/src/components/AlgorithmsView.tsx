import React, { useState, useRef } from 'react';
import { Code, Upload, Plus, ChevronDown, ChevronUp, History, Package, Play, Trash2, FileCode, Tag } from 'lucide-react';
import { cn } from '../lib/utils';

interface AlgoHistory {
  date: string;
  pnl: string;
  status: 'Completed' | 'Stopped' | 'Failed';
}

interface Algo {
  id: string;
  name: string;
  description: string;
  dependencies: string[];
  history: AlgoHistory[];
}

const AlgoWidget = ({ algo }: { algo: Algo }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="group bg-[#171717]/40 backdrop-blur-md border border-neutral-500/20 hover:border-neutral-500/40 rounded-xl overflow-hidden transition-all duration-300">
      <div 
        className="p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-4 flex-1">
          <div className="size-12 bg-white/5 rounded-lg flex items-center justify-center border border-white/10 group-hover:bg-white/10 transition-colors">
            <Code size={24} className="text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white tracking-tight">{algo.name}</h3>
            <p className="text-neutral-400 text-sm line-clamp-1">{algo.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-8 w-full md:w-auto border-t md:border-t-0 border-neutral-800 pt-4 md:pt-0">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-bold mb-1">Dependencies</span>
            <div className="flex gap-1.5">
              {algo.dependencies.slice(0, 3).map((dep, i) => (
                <span key={i} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] text-neutral-300 font-mono">
                  {dep}
                </span>
              ))}
              {algo.dependencies.length > 3 && (
                <span className="text-[10px] text-neutral-500">+{algo.dependencies.length - 3} more</span>
              )}
            </div>
          </div>

          <div className="flex flex-col min-w-[140px]">
            <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-bold mb-1">Recent Run</span>
            <div className="flex items-center gap-2">
              <span className={cn(
                "text-sm font-bold font-mono",
                algo.history[0]?.pnl.startsWith('+') ? "text-green-500" : "text-red-500"
              )}>
                {algo.history[0]?.pnl || 'N/A'}
              </span>
              <span className="text-[10px] text-neutral-500">{algo.history[0]?.date}</span>
            </div>
          </div>

          <button className="hidden md:block p-2 text-neutral-500 hover:text-white transition-colors">
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-6 pb-6 pt-2 border-t border-white/5 animate-in slide-in-from-top-2 duration-300">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
            {/* Full Dependencies */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Package size={16} className="text-neutral-400" />
                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Required Libraries</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {algo.dependencies.map((dep, i) => (
                  <span key={i} className="px-3 py-1 bg-[#262626] border border-neutral-500/30 rounded-md text-xs text-neutral-200 font-mono">
                    {dep}
                  </span>
                ))}
              </div>
            </div>

            {/* Full History */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <History size={16} className="text-neutral-400" />
                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Run History</h4>
              </div>
              <div className="space-y-2">
                {algo.history.map((run, i) => (
                  <div key={i} className="flex items-center justify-between text-sm bg-black/20 p-2.5 rounded-lg border border-white/5">
                    <span className="text-neutral-400 font-mono">{run.date}</span>
                    <div className="flex items-center gap-4">
                      <span className={cn("font-mono font-bold", run.pnl.startsWith('+') ? "text-green-500" : "text-red-500")}>
                        {run.pnl}
                      </span>
                      <span className={cn(
                        "text-[10px] px-2 py-0.5 rounded border uppercase font-bold",
                        run.status === 'Completed' ? "bg-green-500/10 text-green-500 border-green-500/20" : 
                        run.status === 'Stopped' ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" : 
                        "bg-red-500/10 text-red-500 border-red-500/20"
                      )}>
                        {run.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-white/5">
            <button className="flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors text-sm font-medium">
              <Trash2 size={16} />
              Delete
            </button>
            <button className="flex items-center gap-2 px-6 py-2 bg-white text-black rounded-lg hover:bg-neutral-200 transition-colors text-sm font-bold">
              <Play size={16} fill="currentColor" />
              Configure & Run
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const AlgorithmsView = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [algoName, setAlgoName] = useState('');
  const [depsInput, setDepsInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialized as empty for backend population
  const [algos] = useState<Algo[]>([]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.py')) {
      setPendingFile(files[0]);
      // Default name to file name without extension
      setAlgoName(files[0].name.replace('.py', '').split(/[-_]/).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setPendingFile(files[0]);
      setAlgoName(files[0].name.replace('.py', '').split(/[-_]/).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '));
    }
  };

  const resetForm = () => {
    setPendingFile(null);
    setAlgoName('');
    setDepsInput('');
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in duration-500">
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">Algorithm Library</h1>
        <p className="text-neutral-400">Manage your quantitative trading scripts and monitor performance history.</p>
      </header>

      {/* Add Algo Banner */}
      <section className="mb-12">
        {!pendingFile ? (
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "relative h-48 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-300 overflow-hidden",
              isDragging 
                ? "border-white bg-white/10 scale-[1.01]" 
                : "border-neutral-500/30 bg-[#171717]/40 hover:border-neutral-500/60"
            )}
          >
            <input 
              type="file" 
              accept=".py" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileSelect}
            />
            <div className="absolute -right-8 -bottom-8 text-white/5 rotate-12 pointer-events-none">
              <Code size={160} />
            </div>
            
            <div className={cn(
              "size-14 rounded-full flex items-center justify-center transition-all duration-300",
              isDragging ? "bg-white text-black scale-110" : "bg-white/5 text-neutral-400"
            )}>
              <Upload size={28} />
            </div>
            <div className="text-center relative z-10">
              <p className="text-lg font-bold text-white">Drag & drop your Python algorithm</p>
              <p className="text-neutral-500 text-sm">or click to browse files (.py)</p>
            </div>
          </div>
        ) : (
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 animate-in zoom-in-95 duration-300">
            <div className="flex items-start justify-between mb-10">
              <div className="flex items-center gap-4">
                <div className="size-14 bg-green-500/20 rounded-xl flex items-center justify-center border border-green-500/30">
                  <FileCode size={32} className="text-green-500" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">{pendingFile.name}</h3>
                  <p className="text-neutral-400">Configure script details to register the algorithm.</p>
                </div>
              </div>
              <button 
                onClick={resetForm}
                className="text-neutral-500 hover:text-white p-2"
              >
                <Plus size={24} className="rotate-45" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold text-neutral-400 uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                    <Tag size={14} />
                    Algorithm Name *
                  </label>
                  <input 
                    type="text"
                    placeholder="Enter strategy name..."
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-5 py-4 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all font-semibold"
                    value={algoName}
                    onChange={(e) => setAlgoName(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold text-neutral-400 uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                    <Package size={14} />
                    Dependencies (one per line)
                  </label>
                  <textarea 
                    placeholder="pandas&#10;numpy&#10;yfinance"
                    className="w-full h-32 bg-black/40 border border-white/10 rounded-xl px-5 py-4 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all font-mono resize-none leading-relaxed"
                    value={depsInput}
                    onChange={(e) => setDepsInput(e.target.value)}
                  />
                </div>
              </div>
            </div>
            
            <div className="flex justify-end gap-4 mt-10 pt-8 border-t border-white/5">
              <button 
                onClick={resetForm}
                className="px-6 py-3 text-neutral-400 hover:text-white transition-colors font-bold uppercase tracking-widest text-[10px]"
              >
                Cancel
              </button>
              <button className="bg-green-600 hover:bg-green-700 text-white font-bold px-10 py-3 rounded-xl transition-all shadow-lg shadow-green-600/20 flex items-center gap-2 active:scale-95">
                <Plus size={18} />
                <span>Register Algorithm</span>
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Algo List */}
      <section className="space-y-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-bold text-neutral-500 uppercase tracking-[0.2em]">Installed Algorithms ({algos.length})</h2>
        </div>
        <div className="flex flex-col gap-4">
          {algos.map(algo => (
            <AlgoWidget key={algo.id} algo={algo} />
          ))}
        </div>
      </section>
    </div>
  );
};

export default AlgorithmsView;
