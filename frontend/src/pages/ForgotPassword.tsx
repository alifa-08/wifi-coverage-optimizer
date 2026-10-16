import React, { useState } from 'react';
import { KeyRound, ArrowLeft, ArrowRight, RefreshCw, AlertCircle, CheckCircle2, Mail, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';
import { PasswordResetRequestResponse } from '../types';

interface ForgotPasswordProps {
  onBackToLogin: () => void;
  onGoToResetWithToken?: (token: string) => void;
}

export const ForgotPassword: React.FC<ForgotPasswordProps> = ({
  onBackToLogin,
}) => {
  const [identifier, setIdentifier] = useState<string>('DEMO-USN-CSE01');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<PasswordResetRequestResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setErrorMessage('Please enter your College USN or registered email address.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.requestPasswordReset(identifier.trim());
      setResult(res);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMessage(detail);
      } else if (Array.isArray(detail)) {
        setErrorMessage(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '));
      } else {
        setErrorMessage(err.message || 'Unable to process reset request. Please try again.');
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
            onClick={onBackToLogin}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 text-indigo-400" />
            <span>Back to Student Login</span>
          </button>

          <div className="flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
            <span className="text-slate-300 font-medium">Password Recovery System</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
          {/* Header Icon */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
              <Mail className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Reset Wi-Fi Password</h1>
            <p className="text-xs text-slate-400">
              Enter your College USN or registered email to receive a secure, single-use password reset link.
            </p>
          </div>

          {/* Feedback Banner */}
          {result ? (
            <div className={`p-4 rounded-xl border text-xs space-y-3 animate-in fade-in ${
              result.success
                ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                : 'bg-amber-950/30 border-amber-500/40 text-amber-200'
            }`}>
              <div className="flex items-start gap-2.5">
                {result.success ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                )}
                <div className="space-y-1">
                  <span className="font-bold block">
                    {result.success ? 'Request Processed' : 'Email Delivery Notice'}
                  </span>
                  <p className="text-xs leading-relaxed opacity-90">{result.message}</p>
                </div>
              </div>

              {result.success && (
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <span className="block font-semibold text-slate-300">Security Policies:</span>
                  <ul className="list-disc list-inside space-y-0.5">
                    <li>Reset links expire in 15 minutes.</li>
                    <li>Links are strictly single-use and invalidated upon password change.</li>
                    <li>Only approved student accounts can reset credentials.</li>
                  </ul>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="button"
                  onClick={onBackToLogin}
                  className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Return to Student Login</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-2.5 text-rose-200 text-xs animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">
                    <span className="font-semibold block">Request Error</span>
                    <span>{errorMessage}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-300 flex items-center justify-between">
                    <span>College USN or Registered Email</span>
                    <span className="text-[10px] text-slate-500 font-normal">e.g. DEMO-USN-CSE01 or student@campus.edu.in</span>
                  </label>
                  <input
                    type="text"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="Enter USN or registered email"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono"
                    required
                  />
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                  <strong className="text-slate-300">Privacy &amp; Anti-Enumeration:</strong> To protect student privacy, the system returns identical confirmation responses whether an account exists or not, and never exposes registered emails or credentials.
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Processing Request...</span>
                    </>
                  ) : (
                    <>
                      <KeyRound className="w-4 h-4" />
                      <span>Send Password Reset Link</span>
                    </>
                  )}
                </button>
              </form>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-400">Remember your password?</span>
                <button
                  type="button"
                  onClick={onBackToLogin}
                  className="font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer transition-colors"
                >
                  <span>Go to Login</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>Department of Computer Science &amp; Engineering • Final Year Major Project</p>
      </footer>
    </div>
  );
};
