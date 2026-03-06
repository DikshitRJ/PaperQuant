import React from 'react';
import { cn } from '../lib/utils';

interface StatCardProps {
  label: string;
  value: string;
  subValue?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down';
}

export const StatCard = ({ label, value, subValue, icon: Icon, trend }: StatCardProps) => (
  <div className="flex-1 bg-[#171717]/40 backdrop-blur-md border border-neutral-500/40 rounded-xl p-6 shadow-sm">
    <div className="flex items-center justify-between mb-2">
      <span className="text-neutral-400 text-sm font-semibold tracking-wider uppercase">{label}</span>
      <Icon size={18} className="text-neutral-400" />
    </div>
    <div className={cn(
      "text-3xl font-bold mb-2",
      trend === 'up' ? "text-green-500" : trend === 'down' ? "text-red-500" : "text-white"
    )}>
      {value}
    </div>
    {subValue && (
      <div className={cn(
        "inline-flex px-2 py-1 rounded text-sm font-medium",
        trend === 'up' ? "bg-green-500/10 text-green-500 border border-green-500/20" : "bg-red-500/10 text-red-500 border border-red-500/20"
      )}>
        {subValue}
      </div>
    )}
  </div>
);
