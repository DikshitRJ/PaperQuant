import React from 'react';
import { usePaperQuant } from '../context/PaperQuantContext';

export const ExecutionTerminal = () => {
  const { logs } = usePaperQuant();

  return (
    <div className="w-full mt-8 pb-8">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-white text-xl font-bold">Execution Terminal</h3>
        <div className="size-2 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
      </div>
      <div className="bg-[#171717]/60 backdrop-blur-xl border border-neutral-500/40 rounded-xl overflow-hidden shadow-2xl">
        <div className="bg-[#262626]/50 border-b border-neutral-500/40 px-4 py-2 flex items-center justify-between">
          <div className="flex gap-1.5">
            <div className="size-3 bg-neutral-700 rounded-full" />
            <div className="size-3 bg-neutral-700 rounded-full" />
            <div className="size-3 bg-neutral-700 rounded-full" />
          </div>
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">Strategy_Engine_V1.0</span>
          <button className="bg-neutral-700/50 border border-neutral-600/30 rounded px-2 py-0.5 text-[10px] text-neutral-400 hover:text-white transition-colors">
            Clear
          </button>
        </div>
        <div className="bg-[#0a0a0a]/90 p-4 font-mono text-sm h-[300px] overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log, i) => (
              <div key={i} className="flex gap-3 mb-1">
                <span className="text-neutral-600 shrink-0 select-none">{log.time}</span>
                <span className={log.color}>{log.content}</span>
              </div>
            ))
          ) : (
            <div className="text-neutral-500 italic mb-2">Waiting for execution logs...</div>
          )}
          <div className="flex gap-2 items-center mt-2">
            <span className="text-neutral-600">[{new Date().toLocaleTimeString('en-US', { hour12: false })}]</span>
            <div className="w-1.5 h-4 bg-neutral-400 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
};
