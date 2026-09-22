import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Zap, 
  Bell, 
  Cpu, 
  ChevronRight
} from 'lucide-react';
import { cn } from '../lib/utils';
import { usePaperQuant } from '../context/PaperQuantContext';
import { apiClient } from '../lib/api-client';
import { Settings, HealthResponse } from '../types/api';

interface SettingSectionProps {
  icon: React.ElementType;
  title: string;
  description: string;
  children: React.ReactNode;
}

const SettingSection = ({ icon: Icon, title, description, children }: SettingSectionProps) => (
  <section className="mb-8 bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
    <div className="flex items-center gap-3 mb-6">
      <div className="p-2 bg-white/10 rounded-lg">
        <Icon size={20} className="text-neutral-200" />
      </div>
      <div>
        <h2 className="text-xl font-semibold text-white tracking-tight">{title}</h2>
        <p className="text-sm text-neutral-400">{description}</p>
      </div>
    </div>
    {children}
  </section>
);

const Toggle = ({ enabled, onChange, label }: { enabled: boolean, onChange: (val: boolean) => void, label: string }) => (
  <div className="flex items-center justify-between py-2">
    <span className="text-neutral-300 text-sm font-medium">{label}</span>
    <button
      onClick={() => onChange(!enabled)}
      className={cn(
        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none",
        enabled ? "bg-green-600" : "bg-neutral-700"
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
          enabled ? "translate-x-6" : "translate-x-1"
        )}
      />
    </button>
  </div>
);

const SettingsView = () => {
  const { sendNotification } = usePaperQuant();
  const [currency, setCurrency] = useState('USD');
  const [settings, setSettings] = useState<Settings | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  
  const [localFontSize, setLocalFontSize] = useState('14px');

  useEffect(() => {
    apiClient.getSettings().then(setSettings).catch(console.error);
    apiClient.getHealth().then(setHealth).catch(console.error);
  }, []);

  const updateSetting = async (key: string, value: any) => {
    if (!settings) return;
    try {
      const updated = await apiClient.updateSettings({ [key]: value });
      setSettings(updated);
    } catch (e) {
      console.error('Failed to update settings', e);
    }
  };

  const handleToggleAlerts = (val: boolean) => {
    updateSetting('system_alerts', val);
    // Call global setter exposed to window
    (window as any).setNotificationsEnabled?.(val);
    
    if (val) {
      sendNotification("System Alerts Enabled", "You will now receive trade and system notifications.");
    }
  };

  const handleFontSizeChange = (size: string) => {
    setLocalFontSize(size);
    console.log(`Setting font size to ${size}`);
  };

  // Generic flat fee defaults based on currency
  const getFlatFeeLabel = () => {
    switch (currency) {
      case 'INR': return '₹20 Flat Fee';
      case 'EUR': return '€1.00 Flat Fee';
      case 'BTC': return '0.00001 ₿ Flat Fee';
      case 'USD':
      default: return '$1.00 Flat Fee';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 animate-in fade-in duration-500 pb-24">
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">Settings</h1>
        <p className="text-neutral-400 text-lg">Preferences and system configuration for your paper trading environment.</p>
      </header>

      {/* General Preferences */}
      <SettingSection 
        icon={Globe} 
        title="General Preferences" 
        description="Global display and localization settings."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-neutral-500 text-[10px] uppercase font-bold tracking-widest mb-2">Display Currency</label>
            <select 
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all appearance-none text-sm"
            >
              <option value="USD">USD ($) - US Dollar</option>
              <option value="INR">INR (₹) - Indian Rupee</option>
              <option value="EUR">EUR (€) - Euro</option>
              <option value="BTC">BTC (₿) - Bitcoin</option>
            </select>
          </div>
          <div>
            <label className="block text-neutral-500 text-[10px] uppercase font-bold tracking-widest mb-2">App Theme</label>
            <select className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all appearance-none text-sm">
              <option>Deep Black (Default)</option>
              <option>High Contrast</option>
              <option>Classic Terminal (Green)</option>
            </select>
          </div>
        </div>
      </SettingSection>

      {/* Trading Engine */}
      <SettingSection 
        icon={Zap} 
        title="Trading Simulation" 
        description="Configure how the paper trading engine behaves."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-neutral-500 text-[10px] uppercase font-bold tracking-widest mb-2">Simulated Latency</label>
            <select className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all appearance-none text-sm">
              <option>Instant (0ms)</option>
              <option>Realistic (100ms - 300ms)</option>
              <option>High Slippage (500ms+)</option>
            </select>
          </div>
          <div>
            <label className="block text-neutral-500 text-[10px] uppercase font-bold tracking-widest mb-2">Brokerage Commission</label>
            <select className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-white/20 transition-all appearance-none text-sm">
              <option>0.2% of Trade Value</option>
              <option>0.02% of Trade Value</option>
              <option>{getFlatFeeLabel()}</option>
              <option>Zero Commission</option>
            </select>
          </div>
          <div>
            <label className="block text-neutral-500 text-[10px] uppercase font-bold tracking-widest mb-2">Default Leverage</label>
            <div className="relative">
              <input type="number" defaultValue="1" className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-white/20" />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-500 text-xs font-bold">x</span>
            </div>
          </div>
        </div>
      </SettingSection>

      {/* Interface & Feedback */}
      <SettingSection 
        icon={Bell} 
        title="Interface & Feedback" 
        description="Control notifications and UI behavior."
      >
        <div className="space-y-4 max-w-md">
          <Toggle 
            label="Auto-clear logs on new session" 
            enabled={settings?.auto_clear_logs ?? true} 
            onChange={(val) => updateSetting('auto_clear_logs', val)} 
          />
          <Toggle 
            label="Enable desktop system alerts" 
            enabled={settings?.system_alerts ?? true} 
            onChange={handleToggleAlerts} 
          />
          <Toggle 
            label="Sound effects for trades" 
            enabled={settings?.sound_effects ?? false} 
            onChange={(val) => updateSetting('sound_effects', val)} 
          />
          <div className="flex items-center justify-between pt-2">
            <span className="text-neutral-300 text-sm font-medium">Terminal Font Size</span>
            <div className="flex gap-2">
              {['12px', '14px', '16px'].map((size) => (
                <button 
                  key={size}
                  onClick={() => handleFontSizeChange(size)}
                  className={cn(
                    "px-3 py-1 border rounded-md text-[10px] transition-colors",
                    localFontSize === size 
                      ? "bg-white/20 border-white/30 text-white" 
                      : "bg-white/5 border-white/10 text-neutral-400 hover:text-white"
                  )}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        </div>
      </SettingSection>

      {/* System Status */}
      <SettingSection 
        icon={Cpu} 
        title="System Status" 
        description="Core engine health and application details."
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-black/20 p-4 rounded-xl border border-white/5">
            <div className="flex items-center gap-3">
              <div className={cn(
                "size-2 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.5)]",
                health ? "bg-green-500" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"
              )} />
              <span className="text-sm text-neutral-200 font-medium">Python Engine Status</span>
            </div>
            <span className={cn(
              "text-xs font-mono font-bold",
              health ? "text-green-500" : "text-red-500"
            )}>
              {health ? `CONNECTED (v${health.version})` : 'DISCONNECTED'}
            </span>
          </div>
          
          <div className="flex items-center justify-between px-4">
            <div className="flex flex-col">
              <span className="text-white text-sm font-bold">PaperQuant Version</span>
              <span className="text-neutral-500 text-xs">
                {health?.version ? `v${health.version}` : 'Unknown'} (Production Build)
              </span>
            </div>
            <button className="text-xs text-white/40 hover:text-white flex items-center gap-1 transition-colors uppercase font-bold tracking-widest">
              Check for updates
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </SettingSection>
    </div>
  );
};

export default SettingsView;
