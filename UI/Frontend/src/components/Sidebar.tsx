import React from 'react';
import { Home, Play, Code, Settings, Activity } from 'lucide-react';
import { cn } from '../lib/utils';

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  onClick?: () => void;
  isMobile?: boolean;
}

const NavItem = ({ icon: Icon, label, active, onClick, isMobile }: NavItemProps) => (
  <div 
    onClick={onClick}
    className={cn(
      "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all",
      isMobile ? "flex-col gap-1 p-2 flex-1" : "flex-row",
      active 
        ? isMobile 
          ? "text-white" 
          : "bg-white/10 border-l-2 border-white text-white" 
        : "text-slate-400 hover:bg-white/5 hover:text-white"
    )}
  >
    <Icon size={isMobile ? 20 : 18} />
    <span className={cn(
      "font-mono text-xs font-medium",
      !isMobile && "text-sm"
    )}>
      {label}
    </span>
    {isMobile && active && (
      <div className="absolute bottom-1 size-1 bg-white rounded-full" />
    )}
  </div>
);

export const Sidebar = ({ currentView, setView }: { currentView: string, setView: (v: string) => void }) => {
  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 lg:w-80 h-screen bg-[#1a1a1a]/60 backdrop-blur-md border-r border-white/10 p-6 flex-col justify-between shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-10">
            <div className="size-8 bg-white/10 border border-white/20 rounded-lg flex items-center justify-center p-1">
              <Activity size={16} className="text-white" />
            </div>
            <h2 className="text-white text-xl font-bold font-mono tracking-tight">PaperQuant</h2>
          </div>
          
          <nav className="flex flex-col gap-2">
            <NavItem icon={Home} label="Home" active={currentView === 'home'} onClick={() => setView('home')} />
            <NavItem icon={Play} label="Test Algorithm" active={currentView === 'setup' || currentView === 'active'} onClick={() => setView('setup')} />
            <NavItem icon={Code} label="Algorithms" active={currentView === 'algorithms'} onClick={() => setView('algorithms')} />
          </nav>
        </div>

        <NavItem icon={Settings} label="Settings" active={currentView === 'settings'} onClick={() => setView('settings')} />
      </aside>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#1a1a1a]/95 backdrop-blur-lg border-t border-white/10 px-2 py-1 flex justify-around items-center z-50">
        <NavItem isMobile icon={Home} label="Home" active={currentView === 'home'} onClick={() => setView('home')} />
        <NavItem isMobile icon={Play} label="Test" active={currentView === 'setup' || currentView === 'active'} onClick={() => setView('setup')} />
        <NavItem isMobile icon={Code} label="Algos" active={currentView === 'algorithms'} onClick={() => setView('algorithms')} />
        <NavItem isMobile icon={Settings} label="Settings" active={currentView === 'settings'} onClick={() => setView('settings')} />
      </nav>
    </>
  );
};
