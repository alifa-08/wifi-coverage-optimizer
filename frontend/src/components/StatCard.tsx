import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'purple' | 'cyan';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  variant = 'default',
}) => {
  const variantStyles = {
    default: 'border-slate-800 bg-slate-900/60 text-slate-100',
    danger: 'border-rose-900/50 bg-rose-950/20 text-rose-300',
    warning: 'border-amber-900/50 bg-amber-950/20 text-amber-300',
    success: 'border-emerald-900/50 bg-emerald-950/20 text-emerald-300',
    purple: 'border-purple-900/50 bg-purple-950/20 text-purple-300',
    cyan: 'border-cyan-900/50 bg-cyan-950/20 text-cyan-300',
  };

  const iconStyles = {
    default: 'text-indigo-400 bg-indigo-500/10',
    danger: 'text-rose-400 bg-rose-500/10',
    warning: 'text-amber-400 bg-amber-500/10',
    success: 'text-emerald-400 bg-emerald-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    cyan: 'text-cyan-400 bg-cyan-500/10',
  };

  return (
    <div className={`p-4 rounded-xl border backdrop-blur-sm transition-all hover:border-slate-700 shadow-lg ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg ${iconStyles[variant]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-baseline space-x-1">
        <span className="text-2xl font-bold tracking-tight">{value}</span>
        {unit && <span className="text-xs text-slate-400 font-medium">{unit}</span>}
      </div>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
};
