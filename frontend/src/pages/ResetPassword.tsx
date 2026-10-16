import React, { useState, useEffect } from 'react';
import { Lock, CheckCircle2, AlertCircle, RefreshCw, ArrowLeft, ArrowRight, ShieldCheck, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';
import { PasswordResetVerifyTokenResponse } from '../types';

interface ResetPasswordProps {
  token: string;
  onBackToLogin: () => void;
  onGoToForgotPassword: () => void;
}

export const ResetPassword: React.FC<ResetPasswordProps> = ({
  token,
  onBackToLogin,
  onGoToForgotPassword,
}) => {
  const [isVerifying, setIsVerifying] = useState<boolean>(true);
  const [tokenInfo, setTokenInfo] = useState<PasswordResetVerifyTokenResponse | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);

  // Form states
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const verifyToken = async () => {
      if (!token || !token.trim()) {
        setTokenError('No password reset token was provided. Please use the link sent to your registered email.');
        setIsVerifying(false);
        return;
      }

      setIsVerifying(true);
      setTokenError(null);
      try {
        const info = await api.verifyPasswordResetToken(token.trim());
        if (isMounted) {
          setTokenInfo(info);
        }
      } catch (err: any) {
        if (isMounted) {
          const detail = err.response?.data?.detail;
          setTokenError(
            typeof detail === 'string'
              ? detail
              : 'The password reset token is invalid, expired, or has already been used.'
          );
        }
      } finally {
        if (isMounted) {
          setIsVerifying(false);
        }
      }
    };

    verifyToken();
    return () => {
      isMounted = false;
    };
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 6) {
      setSubmitError('New password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setSubmitError('Passwords do not match. Please verify your new password.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await api.confirmPasswordReset({
        token: token.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setIsSuccess(true);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setSubmitError(
        typeof detail === 'string'
          ? detail
          : err.message || 'Failed to reset password. Please try requesting a new link.'
      );
    } finally {
      setIsSubmitting(false);
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
            <span>Cancel and Return to Login</span>
          </button>

          <div className="flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">Verified Gateway Security</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
          {/* Header Icon */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
              <Lock className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Set New Wi-Fi Password</h1>
            <p className="text-xs text-slate-400">
              Create a secure replacement password for your campus Wi-Fi account.
            </p>
          </div>

          {/* Loading verification */}
          {isVerifying ? (
            <div className="py-8 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Verifying security token cryptographic validity...</p>
            </div>
          ) : tokenError ? (
            /* Token Invalid / Expired Screen */
            <div className="p-5 rounded-2xl bg-rose-950/30 border border-rose-500/40 space-y-4 text-xs animate-in fade-in">
              <div className="flex items-start gap-2.5">
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold text-rose-200 block text-sm">Invalid or Expired Reset Link</span>
                  <p className="text-xs text-rose-300 leading-relaxed">{tokenError}</p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span>Possible reasons:</span>
                <ul className="list-disc list-inside space-y-0.5">
                  <li>The 15-minute token lifetime has elapsed.</li>
                  <li>This reset token was already consumed.</li>
                  <li>A newer reset link was requested for this student account.</li>
                </ul>
              </div>

              <div className="pt-2 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={onGoToForgotPassword}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <span>Request a Fresh Reset Link</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={onBackToLogin}
                  className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
                >
                  Back to Login
                </button>
              </div>
            </div>
          ) : isSuccess ? (
            /* Success Screen */
            <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 space-y-4 text-xs animate-in fade-in">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold text-emerald-200 block text-sm">Password Successfully Reset</span>
                  <p className="text-xs text-emerald-300 leading-relaxed">
                    Your password has been updated securely. Your previous credentials and active sessions have been revoked.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={onBackToLogin}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                <span>Proceed to Student Login</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            /* Password Input Form */
            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              {submitError && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-2.5 text-rose-200 text-xs animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">
                    <span className="font-semibold block">Update Error</span>
                    <span>{submitError}</span>
                  </div>
                </div>
              )}

              {/* Masked Account Details */}
              {tokenInfo && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Account USN:</span>
                    <span className="font-mono font-bold text-emerald-300">{tokenInfo.masked_usn}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Student Name:</span>
                    <span className="text-slate-200 font-medium">{tokenInfo.masked_name}</span>
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300 flex items-center justify-between">
                  <span>New Password</span>
                  <span className="text-[10px] text-slate-500 font-normal">Minimum 6 characters</span>
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new secure password"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  required
                  minLength={6}
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  required
                  minLength={6}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Updating Password Credentials...</span>
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    <span>Save New Password &amp; Invalidate Token</span>
                  </>
                )}
              </button>
            </form>
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
