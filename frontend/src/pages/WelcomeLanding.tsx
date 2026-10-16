import React from 'react';
import {
  Wifi,
  KeyRound,
  UserPlus,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Lock,
} from 'lucide-react';

interface WelcomeLandingProps {
  onSelectStudentLogin: () => void;
  onSelectStudentRegister: () => void;
  onSelectAdminLogin: () => void;
}

export const WelcomeLanding: React.FC<WelcomeLandingProps> = ({
  onSelectStudentLogin,
  onSelectStudentRegister,
  onSelectAdminLogin,
}) => {
  const handleAdminClick = () => {
    onSelectAdminLogin();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header / Branding */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-md shadow-indigo-500/20">
              <Wifi className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                Campus AI Wi-Fi &amp; Gateway
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Major Project
                </span>
              </span>
              <span className="text-xs text-slate-400 hidden sm:inline">
                OpenWrt 25.12.5 • OpenNDS 10.3.1 FAS Level 1 • AI RF Optimization
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-300 font-medium">Gateway 192.168.214.2:</span>
              <span className="text-emerald-400 font-bold">ONLINE</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-10 flex flex-col justify-center space-y-10">
        {/* Title and Short Description */}
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
            AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction
          </h1>

          <p className="text-slate-400 text-sm leading-relaxed max-w-2xl mx-auto">
            An intelligent campus Wi-Fi management system that analyzes wireless coverage, predicts connectivity dead zones, and evaluates access-point placement to improve network performance. With OpenWrt-based student authentication and individual data quota management, the platform brings wireless optimization, secure access and network analytics into one integrated solution.
          </p>

          <p className="text-xs text-indigo-400/90 font-medium">
            Simulated and measured results are clearly distinguished to support transparent evaluation.
          </p>
        </div>

        {/* 3 Prominent Main Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
          {/* Action 1: Student Wi-Fi Login */}
          <div
            onClick={onSelectStudentLogin}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') onSelectStudentLogin();
            }}
            className="group relative bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-7 flex flex-col justify-between transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 cursor-pointer text-left"
          >
            <div className="space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                <KeyRound className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
                  Action 1 • Student Area
                </span>
                <h3 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors">
                  Student Wi-Fi Login
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Authenticate your connected device using your College USN and password to access the campus network and inspect your remaining daily quota.
                </p>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-slate-800/80 flex items-center justify-between text-indigo-400 font-semibold text-xs group-hover:text-indigo-300">
              <span className="flex items-center gap-1.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Captive Portal
              </span>
              <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform font-bold text-indigo-400">
                Log In <ArrowRight className="w-4 h-4" />
              </span>
            </div>
          </div>

          {/* Action 2: Student Registration */}
          <div
            onClick={onSelectStudentRegister}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') onSelectStudentRegister();
            }}
            className="group relative bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 rounded-2xl p-7 flex flex-col justify-between transition-all duration-300 hover:shadow-2xl hover:shadow-cyan-500/10 cursor-pointer text-left"
          >
            <div className="space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
                <UserPlus className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">
                  Action 2 • Onboarding
                </span>
                <h3 className="text-xl font-bold text-white group-hover:text-cyan-300 transition-colors">
                  Student Registration
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  New student onboarding for campus Wi-Fi. Supports standard college USN formats with department/batch parsing and automatic administrator review.
                </p>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-slate-800/80 flex items-center justify-between text-cyan-400 font-semibold text-xs group-hover:text-cyan-300">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Lock className="w-4 h-4 text-amber-400" />
                Pending Approval
              </span>
              <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform font-bold text-cyan-400">
                Register <ArrowRight className="w-4 h-4" />
              </span>
            </div>
          </div>

          {/* Action 3: Admin Login */}
          <div
            onClick={handleAdminClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') handleAdminClick();
            }}
            className="group relative bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-emerald-500/50 rounded-2xl p-7 flex flex-col justify-between transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10 cursor-pointer text-left"
          >
            <div className="space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                  Action 3 • Administration
                </span>
                <h3 className="text-xl font-bold text-white group-hover:text-emerald-300 transition-colors">
                  Admin Login
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Campus IT administrator console. Authenticate to approve pending students, manage individual data quotas, monitor gateway netfilter sync, and access AI optimization tools.
                </p>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-slate-800/80 flex items-center justify-between text-emerald-400 font-semibold text-xs group-hover:text-emerald-300">
              <span className="flex items-center gap-1.5 text-slate-300">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Protected Console
              </span>
              <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform font-bold text-emerald-400">
                Admin Login <ArrowRight className="w-4 h-4" />
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* Clean Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>Department of Computer Science &amp; Engineering • Final Year Major Project</p>
      </footer>
    </div>
  );
};
