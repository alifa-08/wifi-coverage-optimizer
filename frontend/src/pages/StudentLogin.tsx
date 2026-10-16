import React, { useState } from 'react';
import { KeyRound, Lock, ArrowLeft, ArrowRight, RefreshCw, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import { StudentLoginResponse } from '../types';

interface StudentLoginProps {
  onBackToWelcome: () => void;
  onGoToRegister: () => void;
  onGoToForgotPassword: () => void;
  onLoginSuccess: (response: StudentLoginResponse, collegeUsn: string) => void;
}

export const StudentLogin: React.FC<StudentLoginProps> = ({
  onBackToWelcome,
  onGoToRegister,
  onGoToForgotPassword,
  onLoginSuccess,
}) => {
  const [collegeUsn, setCollegeUsn] = useState<string>('DEMO-USN-CSE01');
  const [password, setPassword] = useState<string>('Campus@2026');
  const [simulateGateway, setSimulateGateway] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!collegeUsn.trim() || !password) {
      setErrorMessage('Please enter both College USN and Password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.loginStudent({
        college_usn: collegeUsn.trim(),
        password: password,
        client_mac: '00:50:56:c0:00:01',
        client_ip: '192.168.214.1',
        simulate_gateway: simulateGateway,
      });

      onLoginSuccess(res, collegeUsn.trim());
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMessage(detail);
      } else if (Array.isArray(detail)) {
        setErrorMessage(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '));
      } else {
        setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <button
            onClick={onBackToWelcome}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 text-indigo-400" />
            <span>Back to Welcome Screen</span>
          </button>

          <div className="flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-medium">Gateway 192.168.214.2:</span>
            <span className="text-emerald-400 font-bold">ONLINE</span>
          </div>
        </div>
      </header>

      {/* Main Login Form Container */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
          {/* Card Header */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
              <KeyRound className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Student Wi-Fi Login</h1>
            <p className="text-xs text-slate-400">
              Enter your University Serial Number (USN) and password to authenticate on the campus network.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-2.5 text-rose-200 text-xs animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="leading-relaxed">
                <span className="font-semibold block">Authentication Blocked</span>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>College USN</span>
                <span className="text-[10px] text-slate-500 font-normal">e.g. DEMO-USN-CSE01 or ENG23CS0518</span>
              </label>
              <input
                type="text"
                value={collegeUsn}
                onChange={(e) => setCollegeUsn(e.target.value.toUpperCase())}
                placeholder="Enter your College USN"
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                required
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <label>Password</label>
                <button
                  type="button"
                  onClick={onGoToForgotPassword}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium transition-colors cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter account password"
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                required
              />
            </div>

            {/* Viva / Browser Evaluation Mode Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
              <div className="space-y-0.5 pr-2">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Evaluation Mode</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Enables portal evaluation in browser without requiring physical hardware connected on OpenWrt's virtual switch.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={simulateGateway}
                  onChange={(e) => setSimulateGateway(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Credentials &amp; Quota...</span>
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Connect Device to Campus Internet</span>
                </>
              )}
            </button>
          </form>

          {/* Navigation Links */}
          <div className="pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
            <button
              type="button"
              onClick={onGoToForgotPassword}
              className="text-slate-400 hover:text-indigo-300 transition-colors cursor-pointer"
            >
              Trouble logging in? <span className="text-indigo-400 font-semibold underline underline-offset-2">Forgot Password</span>
            </button>
            <button
              onClick={onGoToRegister}
              className="font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer transition-colors"
            >
              <span>Register Account</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>Department of Computer Science &amp; Engineering • Final Year Major Project</p>
      </footer>
    </div>
  );
};
