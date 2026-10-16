import React from 'react';
import {
  LayoutDashboard,
  Users,
  ShieldCheck,
  Map,
  Sparkles,
  Cpu,
  GitCompare,
  BarChart3,
  Bell,
  PlayCircle,
  Activity,
  ArrowLeft,
  Wifi,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'student-management'
  | 'gateway-quotas'
  | 'wifi-coverage'
  | 'dead-zone-prediction'
  | 'ap-optimization'
  | 'before-after'
  | 'network-analytics'
  | 'alerts'
  | 'simulation-testing'
  | 'system-diagnostics';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  deadZoneCount: number;
  alertCount: number;
  onExitAdmin?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  deadZoneCount,
  alertCount,
  onExitAdmin,
}) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: '1. Dashboard', icon: LayoutDashboard },
    { id: 'student-management' as PageId, label: '2. Student Management', icon: Users, highlight: true },
    { id: 'gateway-quotas' as PageId, label: '3. Gateway & Quotas', icon: ShieldCheck, highlight: true },
    { id: 'wifi-coverage' as PageId, label: '4. Wi-Fi Coverage', icon: Map },
    {
      id: 'dead-zone-prediction' as PageId,
      label: '5. Dead-Zone Prediction',
      icon: Sparkles,
      badge: deadZoneCount > 0 ? deadZoneCount : undefined,
      badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
      highlight: true,
    },
    { id: 'ap-optimization' as PageId, label: '6. AP Optimization', icon: Cpu },
    { id: 'before-after' as PageId, label: '7. Before vs After', icon: GitCompare },
    { id: 'network-analytics' as PageId, label: '8. Network Analytics', icon: BarChart3 },
    {
      id: 'alerts' as PageId,
      label: '9. Alerts',
      icon: Bell,
      badge: alertCount > 0 ? alertCount : undefined,
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    },
    { id: 'simulation-testing' as PageId, label: '10. Simulation & Testing', icon: PlayCircle },
    { id: 'system-diagnostics' as PageId, label: '11. System Diagnostics', icon: Activity },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 selection:bg-indigo-500 selection:text-white">
      <div className="space-y-4">
        <div>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2 flex items-center justify-between">
            <span>Admin Console</span>
            <span className="font-mono text-emerald-400">11 Modules</span>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all text-left cursor-pointer ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-bold'
                      : item.highlight
                      ? 'text-slate-200 hover:bg-slate-800 hover:text-white'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? 'text-white' : item.highlight ? 'text-indigo-400' : 'text-slate-400'
                      }`}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {item.badge !== undefined && (
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full border ${
                        isActive ? 'bg-white/20 text-white border-white/30' : item.badgeColor
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Return to Welcome Screen / Logout */}
      <div className="space-y-3 pt-3 border-t border-slate-800/80">
        {onExitAdmin && (
          <button
            onClick={onExitAdmin}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-300 hover:text-white transition-all shadow-sm cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-indigo-400" />
            <span>Exit to Welcome Screen</span>
          </button>
        )}

        {/* Footer Info */}
        <div className="px-2 text-[10px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Gateway 25.12.5:</span>
            <span className="font-mono text-emerald-400 font-bold">192.168.214.2</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Accounting:</span>
            <span className="text-slate-300 font-medium">1 GiB = 1,024 MiB</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
