import React from 'react';
import { Wifi, AlertCircle, LogOut, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  activeAlertCount: number;
  onExitAdmin?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeAlertCount,
  onExitAdmin,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full bg-slate-900/95 backdrop-blur-md border-b border-slate-800">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-md shadow-indigo-500/20">
            <Wifi className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              Campus AI Wi-Fi &amp; Gateway Management
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Administrator Suite
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              OpenWrt 25.12.5 &bull; OpenNDS 10.3.1 FAS Level 1 &bull; AI Dead-Zone Analytics
            </p>
          </div>
        </div>

        {/* Status Indicators & Exit Admin Action */}
        <div className="flex items-center space-x-3">
          {/* Live Gateway Pill */}
          <div className="hidden sm:flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-medium">Gateway 192.168.214.2:</span>
            <span className="text-emerald-400 font-bold">ONLINE</span>
          </div>

          {/* Active Alerts Pill */}
          {activeAlertCount > 0 && (
            <div className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{activeAlertCount} Alerts</span>
            </div>
          )}

          {/* Exit Admin Button */}
          {onExitAdmin && (
            <button
              onClick={onExitAdmin}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-colors cursor-pointer"
              title="Return to Welcome Screen & Clear Session"
            >
              <LogOut className="w-3.5 h-3.5 text-rose-400" />
              <span>Exit Admin</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
