import React, { useState, useMemo } from 'react';
import { UserPlus, Lock, ArrowLeft, ArrowRight, RefreshCw, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';
import { StudentRegistrationResponse } from '../types';

interface StudentRegisterProps {
  onBackToWelcome: () => void;
  onGoToLogin: () => void;
}

export const StudentRegister: React.FC<StudentRegisterProps> = ({
  onBackToWelcome,
  onGoToLogin,
}) => {
  const [usn, setUsn] = useState<string>('ENG23CS0518');
  const [fullName, setFullName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [regResult, setRegResult] = useState<StudentRegistrationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Dynamic USN Regex parsing for instant UI feedback
  const parsedUsnInfo = useMemo(() => {
    const clean = usn.trim().toUpperCase();
    const match = clean.match(/^ENG(\d{2})([A-Z]{2})(\d{3,4})$/);
    if (!match) return null;

    const [_, yearStr, branchCode, rollStr] = match;
    const batchYear = 2000 + parseInt(yearStr, 10);
    const branchMap: Record<string, string> = {
      CS: 'Computer Science Core',
      CT: 'Computer Technology',
      IT: 'Information Technology',
      EC: 'Electronics & Communication',
      ME: 'Mechanical Engineering',
    };
    const deptName = branchMap[branchCode] || `Department (${branchCode})`;
    return {
      batchYear,
      deptName,
      branchCode,
      rollStr,
    };
  }, [usn]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usn.trim()) {
      setErrorMessage('Please enter your College USN.');
      return;
    }
    if (!fullName.trim()) {
      setErrorMessage('Please enter your full student name.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter a password.');
      return;
    }
    if (confirmPassword && password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please re-enter.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.registerStudent({
        college_usn: usn.trim(),
        name: fullName.trim(),
        password: password,
        email: email.trim() || undefined,
      });

      setRegResult(res);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMessage(detail);
      } else if (Array.isArray(detail)) {
        setErrorMessage(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '));
      } else {
        setErrorMessage(err.message || 'Registration failed. Please check inputs.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <button
            onClick={onBackToWelcome}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 text-cyan-400" />
            <span>Back to Welcome Screen</span>
          </button>

          <div className="flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-medium">Gateway 192.168.214.2:</span>
            <span className="text-emerald-400 font-bold">ONLINE</span>
          </div>
        </div>
      </header>

      {/* Main Registration Form Container */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-lg bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
          {/* Card Header */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
              <UserPlus className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Student Wi-Fi Registration</h1>
            <p className="text-xs text-slate-400">
              Submit your university credentials for campus network onboarding and daily quota allocation.
            </p>
          </div>

          {/* Success Banner (when submitted successfully) */}
          {regResult ? (
            <div className="p-5 rounded-2xl bg-amber-950/30 border border-amber-500/40 space-y-4 animate-in fade-in">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-white">Registration Submitted Successfully!</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {regResult.message || 'Your account has been recorded and submitted for administrator approval.'}
                  </p>
                </div>
              </div>

              {/* Account Summary Details */}
              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Registered USN:</span>
                  <span className="font-mono font-bold text-cyan-300">{regResult.college_usn}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Department:</span>
                  <span className="text-slate-200 font-medium">{regResult.department}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Academic Year:</span>
                  <span className="text-slate-200 font-medium">{regResult.academic_year}</span>
                </div>
                <div className="flex items-center justify-between pt-1 border-t border-slate-800">
                  <span className="text-slate-400">Approval Status:</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    {regResult.approval_status}
                  </span>
                </div>
              </div>

              {/* Fail-Closed Notice */}
              <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 flex items-start gap-2 text-[11px] text-slate-400">
                <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Fail-Closed Security:</strong> Wi-Fi internet access remains blocked until a campus administrator reviews and approves your registration in the administrator console.
                </span>
              </div>

              {/* Action */}
              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={onGoToLogin}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>Proceed to Student Login</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            /* Registration Form */
            <>
              {errorMessage && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-2.5 text-rose-200 text-xs animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">
                    <span className="font-semibold block">Registration Error</span>
                    <span>{errorMessage}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* College USN */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>College USN</span>
                    <span className="text-[10px] text-slate-500 font-normal">Format: ENG&lt;YY&gt;&lt;BRANCH&gt;&lt;ROLL&gt;</span>
                  </label>
                  <input
                    type="text"
                    value={usn}
                    onChange={(e) => setUsn(e.target.value.toUpperCase())}
                    placeholder="e.g. ENG23CS0518"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    required
                  />

                  {/* Dynamic USN validation badge */}
                  {parsedUsnInfo && (
                    <div className="mt-1.5 p-2 rounded-lg bg-cyan-950/30 border border-cyan-800/40 flex items-center justify-between text-[11px] text-cyan-300 animate-in fade-in">
                      <span className="font-semibold">{parsedUsnInfo.deptName}</span>
                      <span className="font-mono text-slate-400">Batch {parsedUsnInfo.batchYear}</span>
                    </div>
                  )}
                </div>

                {/* Full Name */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Student Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    required
                  />
                </div>

                {/* College Email (Optional) */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>College Email</span>
                    <span className="text-[10px] text-slate-500 font-normal">Optional</span>
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. rahul.sharma@college.edu.in"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                  />
                </div>

                {/* Password Fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Password</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Account password"
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                      required
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Confirm Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat password"
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/30 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
                >
                  {isLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Submitting Registration...</span>
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4" />
                      <span>Submit Registration for Approval</span>
                    </>
                  )}
                </button>
              </form>

              {/* Navigation Link */}
              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-400">Already registered?</span>
                <button
                  onClick={onGoToLogin}
                  className="font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
                >
                  <span>Go to Student Login</span>
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
