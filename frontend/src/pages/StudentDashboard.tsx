import React from 'react';
import { Wifi, ShieldCheck, HardDrive, ArrowUpRight, ArrowDownRight, Clock, LogOut, CheckCircle2 } from 'lucide-react';
import { StudentLoginResponse } from '../types';

interface StudentDashboardProps {
  loginData: StudentLoginResponse;
  collegeUsn: string;
  onLogout: () => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  loginData,
  collegeUsn,
  onLogout,
}) => {
  const remainingMb = loginData.remaining_quota_mb ?? 1024.0;
  const assignedMb = loginData.assigned_quota_mb ?? 1024.0;
  const uploadMb = loginData.upload_quota_mb ?? 153.6;
  const downloadMb = loginData.download_quota_mb ?? 870.4;
  const timeoutMins = loginData.session_timeout_mins ?? 120;
  const clientMac = loginData.client_mac || '00:50:56:c0:00:01';
  const percentRemaining = Math.max(0, Math.min(100, Math.round((remainingMb / assignedMb) * 100)));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-md shadow-emerald-500/20">
              <Wifi className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                Campus Student Wi-Fi
                <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                  loginData.is_simulated
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}>
                  {loginData.is_simulated ? 'Evaluation Mode' : 'Connected (Live Gateway)'}
                </span>
              </span>
              <span className="text-xs text-slate-400 font-mono">
                USN: {collegeUsn}
              </span>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition-colors border border-slate-700 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5 text-rose-400" />
            <span>Disconnect / Logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full p-6 space-y-6 flex flex-col justify-center">
        {/* Connection Confirmed Card */}
        <div className={`p-6 rounded-2xl bg-gradient-to-r ${
          loginData.is_simulated ? 'from-amber-950/30 via-slate-900 to-slate-900 border-amber-500/40' : 'from-emerald-950/30 via-slate-900 to-slate-900 border-emerald-500/40'
        } border shadow-xl space-y-3`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className={`p-2.5 rounded-xl ${loginData.is_simulated ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'}`}>
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">
                  {loginData.is_simulated ? 'Evaluation Session Recorded' : 'Device Authorized for Campus Internet'}
                </h1>
                <p className="text-xs text-slate-400">
                  {loginData.is_simulated
                    ? 'Offline evaluation session recorded in application ledger (live OpenWrt unchanged).'
                    : 'OpenWrt gateway netfilter rules activated for your hardware address.'}
                </p>
              </div>
            </div>

            <div className="hidden sm:block text-right">
              <span className="text-xs text-slate-400 block">Gateway Address</span>
              <span className="text-xs font-mono font-bold text-emerald-300">192.168.214.2:2050</span>
            </div>
          </div>
        </div>

        {/* Daily Quota Meter */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-indigo-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Daily Bandwidth Allowance (Binary IEC)
              </h2>
            </div>
            <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 px-2.5 py-0.5 rounded-full border border-indigo-500/20">
              1 GiB = 1,024 MiB
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex items-end justify-between">
              <div>
                <div className="text-2xl font-extrabold text-white">
                  {remainingMb.toFixed(1)} <span className="text-sm font-semibold text-slate-400">MiB Available</span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Assigned daily limit: <span className="font-semibold text-slate-200">{assignedMb.toFixed(1)} MiB</span>
                </div>
              </div>

              <div className="text-right font-bold text-emerald-400 text-sm">
                {percentRemaining}% remaining
              </div>
            </div>

            {/* Quota Progress Bar */}
            <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                style={{ width: `${percentRemaining}%` }}
              />
            </div>
          </div>

          {/* Directional Split */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5 text-indigo-400" />
                  Upload Quota
                </span>
                <span className="text-[10px] text-slate-500">15%</span>
              </div>
              <div className="text-base font-bold font-mono text-indigo-300">
                {uploadMb.toFixed(1)} MiB
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" />
                  Download Quota
                </span>
                <span className="text-[10px] text-slate-500">85%</span>
              </div>
              <div className="text-base font-bold font-mono text-emerald-300">
                {downloadMb.toFixed(1)} MiB
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  Session Timeout
                </span>
                <span className="text-[10px] text-slate-500">Auto-reset</span>
              </div>
              <div className="text-base font-bold font-mono text-amber-300">
                {timeoutMins} mins
              </div>
            </div>
          </div>
        </div>

        {/* Security & Client Details */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <span className="font-semibold text-slate-200 block">OpenNDS Session State</span>
              <span className="text-[11px] text-slate-400 font-mono">Client MAC: {clientMac}</span>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700 cursor-pointer"
          >
            End Session &amp; Exit
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>Department of Computer Science &amp; Engineering • Final Year Major Project</p>
      </footer>
    </div>
  );
};
