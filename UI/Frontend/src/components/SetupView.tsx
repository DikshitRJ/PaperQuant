import React from 'react';
import { Play, Search, Plus, Trash2, Wallet, Layers } from 'lucide-react';
import { cn } from '../lib/utils';

interface SetupViewProps {
  onStart: () => void;
}

interface WatchlistItem {
  ticker: string;
  capital: string;
}

const SetupView = ({ onStart }: SetupViewProps) => {
  const [watchlist, setWatchlist] = React.useState<WatchlistItem[]>([]);
  const [tickerInput, setTickerInput] = React.useState('');

  const addTicker = () => {
    const ticker = tickerInput.toUpperCase();
    if (ticker && !watchlist.some(item => item.ticker === ticker)) {
      setWatchlist([...watchlist, { ticker, capital: '1000' }]);
      setTickerInput('');
    }
  };

  const removeTicker = (ticker: string) => {
    setWatchlist(watchlist.filter(item => item.ticker !== ticker));
  };

  const updateCapital = (ticker: string, newCapital: string) => {
    setWatchlist(watchlist.map(item => 
      item.ticker === ticker ? { ...item, capital: newCapital } : item
    ));
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 animate-in fade-in duration-500">
      <header className="mb-8 md:mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">Paper Trading Dashboard</h1>
        <p className="text-neutral-400 text-base md:text-lg">
          Configure your watchlist and allocate simulated capital per stock before execution.
        </p>
      </header>

      <div className="space-y-6 md:space-y-8">
        {/* Strategy Selection */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Layers size={20} className="text-neutral-400" />
            <h2 className="text-lg md:text-xl font-semibold text-white">Algorithm Strategy</h2>
          </div>
          <div className="bg-[#171717]/40 backdrop-blur-md border border-neutral-500/40 rounded-xl p-4 md:p-6 shadow-xl">
            <label className="block text-neutral-400 text-sm font-medium mb-2">Select a script...</label>
            <select defaultValue="" className="w-full bg-[#262626] border border-neutral-500/40 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all appearance-none text-sm md:text-base">
              <option value="" disabled>Select a strategy...</option>
              {/* Options will be populated from backend */}
            </select>
          </div>

        </section>

        {/* Watchlist Configuration */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Search size={20} className="text-neutral-400" />
            <h2 className="text-lg md:text-xl font-semibold text-white">Watchlist & Capital Allocation</h2>
          </div>
          <div className="bg-[#171717]/40 backdrop-blur-md border border-neutral-500/40 rounded-xl p-4 md:p-8 shadow-xl">
            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 mb-6 md:mb-8">
              <div className="flex-1 relative">
                <input 
                  type="text" 
                  placeholder="Ticker (e.g. AAPL)..."
                  className="w-full bg-[#262626] border border-neutral-500/40 rounded-lg pl-10 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all text-sm md:text-base"
                  value={tickerInput}
                  onChange={(e) => setTickerInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTicker()}
                />
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
              </div>
              <button 
                onClick={addTicker}
                className="bg-white text-black font-bold px-6 py-3 rounded-lg hover:bg-neutral-200 transition-colors flex items-center justify-center gap-2 text-sm md:text-base"
              >
                <Plus size={18} />
                <span>Add Ticker</span>
              </button>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {watchlist.map((item) => (
                <div key={item.ticker} className="flex flex-col sm:flex-row sm:items-center justify-between bg-[#262626]/60 border border-neutral-500/40 rounded-lg p-4 md:px-6 md:py-4 gap-4">
                  <div className="flex items-center gap-4">
                    <div className="size-10 bg-white/5 border border-neutral-500/40 rounded-full flex items-center justify-center font-bold text-white shrink-0">
                      {item.ticker.slice(0, 2)}
                    </div>
                    <span className="text-white font-semibold text-lg tracking-wider w-20">{item.ticker}</span>
                  </div>
                  
                  <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto border-t sm:border-t-0 border-neutral-700/50 pt-3 sm:pt-0">
                    <div className="flex items-center gap-2">
                      <span className="text-neutral-400 text-xs md:text-sm font-medium">Capital:</span>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500 font-medium">$</span>
                        <input 
                          type="number" 
                          value={item.capital}
                          onChange={(e) => updateCapital(item.ticker, e.target.value)}
                          className="w-28 md:w-32 bg-[#1a1a1a] border border-neutral-500/40 rounded-md pl-7 pr-3 py-1.5 text-white font-mono text-sm focus:outline-none focus:ring-1 focus:ring-white/30 transition-all"
                        />
                      </div>
                    </div>
                    <div className="hidden sm:block w-px h-6 bg-neutral-600/50 mx-2" />
                    <button 
                      onClick={() => removeTicker(item.ticker)}
                      className="text-neutral-500 hover:text-red-500 transition-colors p-2 rounded-md hover:bg-red-500/10"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              ))}
              {watchlist.length === 0 && (
                <div className="text-center py-8 text-neutral-500 italic">
                  No tickers added. Search above to add stocks to your watchlist.
                </div>
              )}
            </div>
          </div>
        </section>

        <div className="pt-8 flex flex-col sm:flex-row justify-end gap-4">
          <button 
            onClick={onStart}
            disabled={watchlist.length === 0}
            className="flex items-center justify-center gap-3 bg-green-600 text-white font-bold px-10 py-4 rounded-xl hover:bg-green-700 transition-all shadow-lg shadow-green-600/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:shadow-none w-full sm:w-auto"
          >
            <Play size={24} fill="currentColor" />
            <span className="text-lg md:text-xl uppercase tracking-widest">Start Session</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SetupView;
