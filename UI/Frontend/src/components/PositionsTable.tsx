import { MoreVertical } from 'lucide-react';
import { cn } from '../lib/utils';
import { usePaperQuant } from '../context/PaperQuantContext';

export const PositionsTable = () => {
  const { positions } = usePaperQuant();

  return (
    <div className="w-full mt-8">
      <h3 className="text-white text-xl font-bold mb-4">Active Positions</h3>
      <div className="bg-[#171717]/40 backdrop-blur-md border border-neutral-500/40 rounded-xl overflow-x-auto shadow-sm scrollbar-thin scrollbar-thumb-white/10">
        <table className="w-full text-left border-collapse min-w-[600px] md:min-w-full">
          <thead className="bg-[#262626]/40 border-b border-neutral-500/40">
            <tr>
              <th className="px-6 py-4 text-xs font-bold text-neutral-400 uppercase tracking-wider">Ticker</th>
              <th className="px-6 py-4 text-xs font-bold text-neutral-400 uppercase tracking-wider">Net P&L</th>
              <th className="px-6 py-4 text-xs font-bold text-neutral-400 uppercase tracking-wider">Invested Value</th>
              <th className="px-6 py-4 text-xs font-bold text-neutral-400 uppercase tracking-wider">Current Value</th>
              <th className="px-6 py-4 text-xs font-bold text-neutral-400 uppercase tracking-wider text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-500/40">
            {positions.length > 0 ? (
              positions.map((pos, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="size-8 bg-[#262626] border border-neutral-500/40 rounded-full flex items-center justify-center text-xs font-bold text-white uppercase">
                        {pos.initials}
                      </div>
                      <span className="text-white text-sm font-medium">{pos.ticker}</span>
                    </div>
                  </td>
                  <td className={cn(
                    "px-6 py-4 text-sm font-semibold",
                    pos.pnl.startsWith('+') ? "text-green-500" : "text-red-500"
                  )}>
                    {pos.pnl}
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-300 font-mono">{pos.invested}</td>
                  <td className="px-6 py-4 text-sm text-neutral-300 font-mono">{pos.current}</td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-neutral-400 hover:text-white transition-colors">
                      <MoreVertical size={16} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-neutral-500 italic">
                  No active positions.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
