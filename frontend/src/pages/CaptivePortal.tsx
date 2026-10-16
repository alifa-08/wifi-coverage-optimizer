import React, { useState, useMemo, useEffect } from 'react';
import {
  ShieldCheck,
  Lock,
  User,
  Wifi,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Radio,
  Server,
  Clock,
  HardDrive,
  Info,
  KeyRound,
  GraduationCap,
  Calendar,
  Layers,
  UserPlus,
  History,
  HelpCircle,
  Check,
  AlertTriangle,
  RefreshCw,
  Search,
} from 'lucide-react';
import { api } from '../api/client';
import {
  StudentLoginResponse,
  DemoOtpResponse,
  StudentRegistrationResponse,
  StudentSelfProfile,
} from '../types';
import { PageId } from '../components/Sidebar';

interface CaptivePortalProps {
  onNavigate: (page: PageId) => void;
  initialTab?: 'login' | 'register' | 'profile' | 'help';
  onReturnToWelcome?: () => void;
}

export const CaptivePortal: React.FC<CaptivePortalProps> = ({
  onNavigate,
  initialTab = 'login',
  onReturnToWelcome,
}) => {
  const [activeTab, setActiveTab] = useState<'login' | 'register' | 'profile' | 'help'>(initialTab);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  // --- Login State ---
  const [collegeUsn, setCollegeUsn] = useState<string>('DEMO-USN-CSE01');
  const [password, setPassword] = useState<string>('Campus@2026');
  const [clientMac, setClientMac] = useState<string>('00:50:56:c0:00:01');
  const [clientIp, setClientIp] = useState<string>('192.168.214.1');
  const [redirUrl, setRedirUrl] = useState<string>('https://www.google.com');

  // Demo OTP Simulator state
  const [useOtp, setUseOtp] = useState<boolean>(false);
  const [otpCode, setOtpCode] = useState<string>('');
  const [demoOtpInfo, setDemoOtpInfo] = useState<DemoOtpResponse | null>(null);
  const [isRequestingOtp, setIsRequestingOtp] = useState<boolean>(false);
  const [simulateGateway, setSimulateGateway] = useState<boolean>(true);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loginResult, setLoginResult] = useState<StudentLoginResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // --- Registration State ---
  const [regUsn, setRegUsn] = useState<string>('ENG23CS0518');
  const [regName, setRegName] = useState<string>('');
  const [regPassword, setRegPassword] = useState<string>('');
  const [isRegistering, setIsRegistering] = useState<boolean>(false);
  const [regResult, setRegResult] = useState<StudentRegistrationResponse | null>(null);
  const [regError, setRegError] = useState<string | null>(null);

  // --- Self-Service Profile Lookup State ---
  const [profileUsn, setProfileUsn] = useState<string>('DEMO-USN-CSE01');
  const [profilePassword, setProfilePassword] = useState<string>('Campus@2026');
  const [isFetchingProfile, setIsFetchingProfile] = useState<boolean>(false);
  const [selfProfile, setSelfProfile] = useState<StudentSelfProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Demo Accounts
  const demoAccounts = [
    {
      usn: 'DEMO-USN-CSE01',
      name: 'Aditya Sharma',
      dept: 'Computer Science Core',
      batch: '2023',
      quota: '1,024 MiB (1 GiB)',
      status: 'APPROVED',
      type: 'Normal Allowance',
      desc: 'Standard 1 GiB/day campus quota',
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-950/20 text-emerald-300',
    },
    {
      usn: 'DEMO-USN-IT02',
      name: 'Priya Patel',
      dept: 'Information Technology',
      batch: '2023',
      quota: '2,048 MiB (2 GiB)',
      status: 'APPROVED',
      type: 'Lab Quota',
      desc: 'Extended 2 GiB/day quota',
      color: 'border-cyan-500/40 hover:border-cyan-400 bg-cyan-950/20 text-cyan-300',
    },
    {
      usn: 'DEMO-USN-ECE03',
      name: 'Rohan Verma',
      dept: 'Electronics & Communication',
      batch: '2024',
      quota: '512 MiB',
      status: 'APPROVED',
      type: 'Research Quota',
      desc: 'Research lab 512 MiB/day quota',
      color: 'border-purple-500/40 hover:border-purple-400 bg-purple-950/20 text-purple-300',
    },
    {
      usn: 'DEMO-USN-EXH05',
      name: 'Sneha Rao',
      dept: 'Computer Science Core',
      batch: '2025',
      quota: '0 MiB remaining',
      status: 'APPROVED',
      type: 'Quota Exhausted',
      desc: 'Tests quota-blocked behavior',
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-950/20 text-rose-300',
    },
  ];

  // Interactive Live USN Parser for registration form
  const parsedUsnPreview = useMemo(() => {
    const raw = regUsn.trim().toUpperCase();
    if (!raw) return null;

    const standardMatch = raw.match(/^([A-Z]{3})(\d{2})([A-Z]{2})(\d{3,5})$/);
    if (standardMatch) {
      const [, prefix, yr, deptCode, seq] = standardMatch;
      const batchYear = 2000 + parseInt(yr, 10);
      const deptNames: Record<string, string> = {
        CS: 'Computer Science Core',
        CT: 'Cybersecurity',
        IT: 'Information Technology',
        IS: 'Information Science & Engineering',
        EC: 'Electronics & Communication',
        ME: 'Mechanical Engineering',
        AI: 'AI & Data Science',
        EE: 'Electrical & Electronics Engineering',
      };
      return {
        isValid: true,
        prefix,
        batchYear,
        deptCode,
        deptName: deptNames[deptCode] || `Department (${deptCode})`,
        sequence: seq,
        academicYear: batchYear === 2023 ? '4th Year / Final Year' : batchYear === 2024 ? '3rd Year' : batchYear === 2025 ? '2nd Year' : '1st Year',
      };
    }

    if (raw.startsWith('DEMO-')) {
      return {
        isValid: true,
        prefix: 'DEMO',
        batchYear: 2023,
        deptCode: 'CS',
        deptName: 'Demo Computer Science',
        sequence: '001',
        academicYear: 'Final Year Demo',
      };
    }

    return {
      isValid: false,
      error: 'Expected: 3-letter prefix + 2-digit batch + 2-letter dept + 3-5 digits (e.g. ENG23CS0518, ENG23CT0112)',
    };
  }, [regUsn]);

  const handleSelectDemo = (acc: typeof demoAccounts[0]) => {
    setCollegeUsn(acc.usn);
    setPassword('Campus@2026');
    setErrorMessage(null);
    setLoginResult(null);
    setDemoOtpInfo(null);
    setOtpCode('');
  };

  const handleRequestDemoOtp = async () => {
    setIsRequestingOtp(true);
    setErrorMessage(null);
    try {
      const res = await api.requestDemoOtp(collegeUsn.trim());
      setDemoOtpInfo(res);
      setOtpCode(res.demo_otp);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to generate demo OTP.');
    } finally {
      setIsRequestingOtp(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setLoginResult(null);

    try {
      const res = await api.loginStudent({
        college_usn: collegeUsn.trim(),
        password: password,
        client_mac: clientMac.trim(),
        client_ip: clientIp.trim() || undefined,
        redir_url: redirUrl.trim() || undefined,
        otp_code: useOtp ? otpCode.trim() : undefined,
        simulate_gateway: simulateGateway,
      });
      setLoginResult(res);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Gateway authentication failed. Please check credentials or gateway connectivity.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRegistering(true);
    setRegError(null);
    setRegResult(null);

    try {
      const res = await api.registerStudent({
        college_usn: regUsn.trim().toUpperCase(),
        name: regName.trim(),
        password: regPassword,
      });
      setRegResult(res);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Registration failed.';
      setRegError(msg);
    } finally {
      setIsRegistering(false);
    }
  };

  const handleFetchProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsFetchingProfile(true);
    setProfileError(null);
    setSelfProfile(null);

    try {
      const res = await api.getStudentSelfProfile({
        college_usn: profileUsn.trim().toUpperCase(),
        password: profilePassword,
      });
      setSelfProfile(res);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to retrieve profile.';
      setProfileError(msg);
    } finally {
      setIsFetchingProfile(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Distinction Header Banner */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-3 shadow-lg shadow-black/20">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
            </span>
            <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-indigo-400" />
              College Student Wi-Fi Portal
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            OpenWrt 25.12.5 • OpenNDS 10.3.1 Forward Authentication Service (FAS Level 1) • Individual 1 GiB Binary Daily Quotas
          </p>
        </div>

        <div className="flex items-center gap-2">
          {onReturnToWelcome && (
            <button
              onClick={onReturnToWelcome}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 text-indigo-400" />
              Welcome Screen
            </button>
          )}
          <button
            onClick={() => onNavigate('gateway-quotas')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Admin Portal
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 rounded-xl p-1 gap-1">
        <button
          onClick={() => { setActiveTab('login'); setErrorMessage(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'login'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <KeyRound className="w-4 h-4" />
          Wi-Fi Login &amp; Gateway
        </button>
        <button
          onClick={() => { setActiveTab('register'); setRegError(null); setRegResult(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'register'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <UserPlus className="w-4 h-4" />
          Student Registration
        </button>
        <button
          onClick={() => { setActiveTab('profile'); setProfileError(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'profile'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <History className="w-4 h-4" />
          My Usage &amp; Status
        </button>
        <button
          onClick={() => setActiveTab('help')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'help'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          Quota Policy &amp; Help
        </button>
      </div>

      {/* ======================================================== */}
      {/* TAB 1: Wi-Fi Login & Authentication                      */}
      {/* ======================================================== */}
      {activeTab === 'login' && (
        <div className="space-y-6">
          {/* Demo Accounts Quick-Select */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-1">
              <span>Quick-Fill Demo Student Accounts (Viva / Testing):</span>
              <span className="text-[11px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Demo Accounts Clearly Labeled
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
              {demoAccounts.map((acc) => (
                <button
                  key={acc.usn}
                  type="button"
                  onClick={() => handleSelectDemo(acc)}
                  className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden group ${
                    acc.color
                  } ${collegeUsn === acc.usn ? 'ring-2 ring-indigo-500 shadow-md' : ''}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-100">{acc.usn}</span>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-900/60 border border-slate-700/50">
                      {acc.dept}
                    </span>
                  </div>
                  <div className="text-[11px] font-medium text-slate-300">{acc.name}</div>
                  <div className="text-[11px] font-semibold text-emerald-400 mt-1 flex items-center justify-between">
                    <span>{acc.quota}</span>
                    <span className="text-[10px] text-slate-400">{acc.batch} Batch</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Login Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-indigo-400" />
                Authenticate for Campus Wi-Fi Internet Access
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Enter your College USN and password to authorize your device MAC on the OpenWrt router.
              </p>
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-start gap-3 text-rose-200">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs">
                  <div className="font-bold text-rose-300">Access Denied by Gateway Policy</div>
                  <p className="leading-relaxed">{errorMessage}</p>
                  {errorMessage.includes('pending administrator approval') && (
                    <p className="text-[11px] text-amber-300 mt-1">
                      Tip: Your registration has been received. Please notify the administrator or log in as admin in the Admin Portal to approve this account.
                    </p>
                  )}
                  {errorMessage.includes('quota exhausted') && (
                    <p className="text-[11px] text-amber-300 mt-1">
                      Tip: Your daily 1 GiB quota resets tonight at midnight (00:00). Contact network admin for an emergency extension.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Success State */}
            {loginResult && loginResult.success && (
              <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-emerald-300">
                        Gateway Authorization Granted!
                      </h3>
                      <p className="text-xs text-slate-300 mt-0.5">
                        Welcome, <span className="font-semibold text-white">{loginResult.name}</span> ({loginResult.college_usn})
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    STATUS: ACTIVE
                  </span>
                </div>

                {/* Quota & Session Stats Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Remaining Quota</div>
                    <div className="text-base font-extrabold text-emerald-400 mt-0.5">
                      {loginResult.remaining_quota_mb?.toFixed(1)} <span className="text-xs">MiB</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      of {loginResult.assigned_quota_mb} MiB allowance
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Download Quota</div>
                    <div className="text-base font-extrabold text-indigo-400 mt-0.5">
                      {loginResult.download_quota_mb?.toFixed(1)} <span className="text-xs">MiB</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">85% allocated</div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Upload Quota</div>
                    <div className="text-base font-extrabold text-cyan-400 mt-0.5">
                      {loginResult.upload_quota_mb?.toFixed(1)} <span className="text-xs">MiB</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">15% allocated</div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Session Timeout</div>
                    <div className="text-base font-extrabold text-amber-400 mt-0.5">
                      {loginResult.session_timeout_mins} <span className="text-xs">mins</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Auto-disconnect</div>
                  </div>
                </div>

                {/* OpenNDS Complete Handshake Button */}
                {loginResult.authaction_url && (
                  <div className="pt-2 flex items-center justify-between border-t border-emerald-500/20">
                    <span className="text-xs text-slate-300">
                      OpenNDS FAS Handshake Token: <code className="text-[11px] text-indigo-300 font-mono">{loginResult.tok?.slice(0, 16)}...</code>
                    </span>
                    <a
                      href={loginResult.authaction_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-600/30"
                    >
                      Complete Gateway Handshake
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-indigo-400" />
                    College USN / Student ID
                  </label>
                  <input
                    type="text"
                    value={collegeUsn}
                    onChange={(e) => setCollegeUsn(e.target.value.toUpperCase())}
                    placeholder="e.g. ENG23CS0518 or DEMO-USN-CSE01"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono font-medium"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Lock className="w-4 h-4 text-indigo-400" />
                    Account Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter student password"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              {/* Hardware Device MAC (Auto-detected by Gateway) */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                    <Radio className="w-3.5 h-3.5 text-slate-500" />
                    Device MAC Address
                  </label>
                  <input
                    type="text"
                    value={clientMac}
                    onChange={(e) => setClientMac(e.target.value)}
                    placeholder="00:00:00:00:00:00"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 font-mono"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                    <Server className="w-3.5 h-3.5 text-slate-500" />
                    Assigned IP
                  </label>
                  <input
                    type="text"
                    value={clientIp}
                    onChange={(e) => setClientIp(e.target.value)}
                    placeholder="192.168.214.x"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                    <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                    Destination URL
                  </label>
                  <input
                    type="text"
                    value={redirUrl}
                    onChange={(e) => setRedirUrl(e.target.value)}
                    placeholder="https://www.google.com"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 truncate"
                  />
                </div>
              </div>

              {/* Optional Demo OTP Accordion */}
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useOtp}
                      onChange={(e) => setUseOtp(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-indigo-500 focus:ring-0"
                    />
                    <span className="text-xs font-semibold text-slate-300">
                      Include 2-Factor Demo Verification Code (Optional)
                    </span>
                  </label>
                  {useOtp && (
                    <button
                      type="button"
                      onClick={handleRequestDemoOtp}
                      disabled={isRequestingOtp}
                      className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      {isRequestingOtp ? 'Generating...' : 'Simulate College SMS OTP'}
                    </button>
                  )}
                </div>

                {useOtp && (
                  <div className="space-y-2 pt-1">
                    <input
                      type="text"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      placeholder="Enter 6-digit OTP"
                      maxLength={6}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono"
                    />
                    {demoOtpInfo && (
                      <p className="text-[11px] text-amber-400">
                        Simulated OTP Code: <strong className="font-mono text-white">{demoOtpInfo.demo_otp}</strong> (Expires in 5 mins)
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Viva / Browser Evaluation Mode Toggle */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
                <div className="space-y-0.5">
                  <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    Viva / Browser Evaluation Mode
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Allows evaluating portal login &amp; quota countdown without requiring a physical client connected on OpenWrt's virtual switch.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
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
                className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-600/30"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Authenticating against OpenWrt Gateway...
                  </>
                ) : (
                  <>
                    Connect Device to Campus Internet
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: Student Registration                              */}
      {/* ======================================================== */}
      {activeTab === 'register' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-indigo-400" />
              New Student Account Registration
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Register with your College USN. All accounts require administrator approval before Wi-Fi internet access is activated.
            </p>
          </div>

          {regError && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center gap-3 text-rose-200 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{regError}</span>
            </div>
          )}

          {regResult && regResult.success && (
            <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 space-y-3">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                <div>
                  <h3 className="text-sm font-bold text-emerald-300">Registration Submitted Successfully!</h3>
                  <p className="text-xs text-slate-300 mt-0.5">{regResult.message}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Registered USN</div>
                  <div className="font-bold text-slate-200 mt-0.5">{regResult.college_usn}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Department</div>
                  <div className="font-bold text-slate-200 mt-0.5">{regResult.department}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Batch Year</div>
                  <div className="font-bold text-slate-200 mt-0.5">{regResult.batch_year} ({regResult.academic_year})</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Approval State</div>
                  <div className="font-bold text-amber-400 mt-0.5">{regResult.approval_status}</div>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>College USN / Student Roll Number</span>
                <span className="text-[11px] text-slate-500 font-mono">Format: ENG23CS0518</span>
              </label>
              <input
                type="text"
                value={regUsn}
                onChange={(e) => setRegUsn(e.target.value.toUpperCase())}
                placeholder="e.g. ENG23CS0518, ENG23CT0112"
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 font-mono font-medium focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            {/* Live USN Structure Breakdown Card */}
            {parsedUsnPreview && (
              <div className={`p-4 rounded-xl border text-xs space-y-2 ${
                parsedUsnPreview.isValid
                  ? 'bg-slate-950 border-indigo-500/40 text-slate-300'
                  : 'bg-rose-950/20 border-rose-500/40 text-rose-300'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold flex items-center gap-1.5 text-indigo-300">
                    <Sparkles className="w-3.5 h-3.5" />
                    Real-Time USN Structure Analysis
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    parsedUsnPreview.isValid ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                  }`}>
                    {parsedUsnPreview.isValid ? 'FORMAT VALID' : 'FORMAT INVALID'}
                  </span>
                </div>

                {parsedUsnPreview.isValid ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Institution Prefix</span>
                      <strong className="font-mono text-slate-200">{parsedUsnPreview.prefix}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Admission Batch</span>
                      <strong className="font-mono text-indigo-300">{parsedUsnPreview.batchYear} Batch</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Branch / Department</span>
                      <strong className="text-slate-200">{parsedUsnPreview.deptName}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Student Roll ID</span>
                      <strong className="font-mono text-slate-200">#{parsedUsnPreview.sequence}</strong>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-rose-300">{parsedUsnPreview.error}</p>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Student Full Name</label>
                <input
                  type="text"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="e.g. Rahul Sharma"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Set Account Password</label>
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  required
                  minLength={6}
                />
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div className="font-bold text-slate-300 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Fair Internet Access Policy:
              </div>
              <p>
                Each student is allotted <strong>1,024 MiB (1 GiB)</strong> of daily high-speed campus internet. Internet access is blocked automatically when the quota is exhausted and resets every night at midnight.
              </p>
            </div>

            <button
              type="submit"
              disabled={isRegistering || !parsedUsnPreview?.isValid}
              className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-600/30"
            >
              {isRegistering ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Submitting Student Registration...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Submit Registration for Approval
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: My Usage & Status (Private Self-Profile)          */}
      {/* ======================================================== */}
      {activeTab === 'profile' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <History className="w-5 h-5 text-indigo-400" />
              Student Self-Service Portal &amp; Usage History
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Securely view your account approval state, daily quota consumption, remaining data, and session history.
            </p>
          </div>

          {/* Profile Lookup Credentials Form */}
          <form onSubmit={handleFetchProfile} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400">College USN</label>
                <input
                  type="text"
                  value={profileUsn}
                  onChange={(e) => setProfileUsn(e.target.value.toUpperCase())}
                  placeholder="e.g. DEMO-USN-CSE01 or ENG23CS0518"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400">Password</label>
                <input
                  type="password"
                  value={profilePassword}
                  onChange={(e) => setProfilePassword(e.target.value)}
                  placeholder="Enter account password"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={isFetchingProfile}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              {isFetchingProfile ? 'Looking up record...' : 'View My Account & History'}
            </button>
          </form>

          {profileError && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{profileError}</span>
            </div>
          )}

          {selfProfile && (
            <div className="space-y-6 pt-2">
              {/* Profile Card */}
              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{selfProfile.name}</h3>
                    <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                      <span className="font-mono text-indigo-400 font-semibold">{selfProfile.college_usn}</span>
                      <span>•</span>
                      <span>{selfProfile.department}</span>
                      <span>•</span>
                      <span>{selfProfile.academic_year} ({selfProfile.batch_year} Batch)</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${
                      selfProfile.approval_status === 'APPROVED'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : selfProfile.approval_status === 'PENDING_APPROVAL'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}>
                      {selfProfile.approval_status}
                    </span>
                    {selfProfile.is_demo && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                        DEMO ACCOUNT
                      </span>
                    )}
                  </div>
                </div>

                {/* Daily Quota Visual Progress */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Daily Binary Data Allowance</span>
                    <span className="font-semibold text-slate-200">
                      {selfProfile.used_quota_mb.toFixed(1)} MiB used / {selfProfile.daily_quota_mb} MiB allotted
                    </span>
                  </div>
                  <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full transition-all rounded-full ${
                        selfProfile.remaining_quota_mb <= 0
                          ? 'bg-rose-500'
                          : selfProfile.remaining_quota_mb < 200
                          ? 'bg-amber-500'
                          : 'bg-indigo-500'
                      }`}
                      style={{
                        width: `${Math.min(100, (selfProfile.used_quota_mb / selfProfile.daily_quota_mb) * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500">
                    <span>Reset Policy: {selfProfile.quota_reset_time}</span>
                    <span className="font-bold text-emerald-400">
                      {selfProfile.remaining_quota_mb.toFixed(1)} MiB Remaining
                    </span>
                  </div>
                </div>
              </div>

              {/* Recent Sessions */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <Clock className="w-3.5 h-3.5 text-indigo-400" />
                  Recent Device Connection Sessions
                </h4>
                {selfProfile.recent_sessions.length === 0 ? (
                  <p className="text-xs text-slate-500 p-4 rounded-xl bg-slate-950 text-center">
                    No active or past sessions recorded for this student device.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {selfProfile.recent_sessions.map((sess) => (
                      <div
                        key={sess.id}
                        className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-mono text-slate-200 font-semibold">{sess.client_mac}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            Started: {new Date(sess.session_start).toLocaleTimeString()}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            sess.status === 'ACTIVE'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}>
                            {sess.status}
                          </span>
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            {(sess.quota_assigned_kb / 1024).toFixed(0)} MiB quota
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: Quota Policy & Help Desk                          */}
      {/* ======================================================== */}
      {activeTab === 'help' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-indigo-400" />
              Campus Wi-Fi Policy &amp; Help Desk
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Guidelines on data allowance, access policies, and resolving connectivity issues.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="font-bold text-slate-200 flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-indigo-400" />
                Daily Binary Data Quota (1 GiB)
              </div>
              <p className="text-slate-400 leading-relaxed">
                The network utilizes consistent binary units: <strong>1 GiB = 1,024 MiB = 1,048,576 KiB</strong>. Each registered and approved student receives 1 GiB per day. Uploads and downloads are tracked cumulatively to prevent overconsumption.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="font-bold text-slate-200 flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                Automatic Midnight Reset Policy
              </div>
              <p className="text-slate-400 leading-relaxed">
                Quotas reset every day at <strong>00:00 (Midnight)</strong>. Once a student reaches their limit, the OpenWrt router blocks further external traffic until the midnight reset or an administrator grant.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="font-bold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-amber-400" />
                Administrator Approval Requirement
              </div>
              <p className="text-slate-400 leading-relaxed">
                For security and abuse prevention, new registrations enter a <span className="text-amber-300 font-semibold">PENDING_APPROVAL</span> state. Campus network administrators must review student roll numbers before granting internet access.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="font-bold text-slate-200 flex items-center gap-2">
                <Radio className="w-4 h-4 text-cyan-400" />
                Coverage Optimization Integration
              </div>
              <p className="text-slate-400 leading-relaxed">
                Slow speeds in specific classrooms can be caused by physical dead zones rather than quota exhaustion. Our system combines AI signal mapping to diagnose weak RF coverage across campus floors.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-xs space-y-2">
            <h4 className="font-bold text-indigo-300">Need Administrator Assistance?</h4>
            <p className="text-slate-400">
              For emergency quota resets, account activation, or dead zone reporting, please visit the IT Support Office in Academic Block 1 or contact the network administrator through the Campus Admin Portal.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
