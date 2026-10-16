import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Activity,
  Wifi,
  Users,
  HardDrive,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Server,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Radio,
  Sparkles,
  Lock,
  UserPlus,
  Edit,
  Power,
  FileText,
  KeyRound,
  LogOut,
  Search,
  Filter,
  Check,
  X,
  UserCheck,
  UserX,
} from 'lucide-react';
import { api, adminAuth } from '../api/client';
import {
  GatewayStatus,
  GatewayTelemetry,
  Student,
  GatewayLiveClient,
  GatewaySession,
  AdminUser,
  GatewayEvent,
} from '../types';
import { StatCard } from '../components/StatCard';
import { PageId } from '../components/Sidebar';

interface GatewayManagementProps {
  onNavigate: (page: PageId) => void;
}

export const GatewayManagement: React.FC<GatewayManagementProps> = ({ onNavigate }) => {
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [telemetry, setTelemetry] = useState<GatewayTelemetry | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [liveClients, setLiveClients] = useState<GatewayLiveClient[]>([]);
  const [history, setHistory] = useState<GatewaySession[]>([]);
  const [events, setEvents] = useState<GatewayEvent[]>([]);

  const [activeTab, setActiveTab] = useState<'roster' | 'events'>('roster');

  // Administrator state
  const [isAdmin, setIsAdmin] = useState<boolean>(adminAuth.isAuthenticated());
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [showAdminModal, setShowAdminModal] = useState<boolean>(false);
  const [adminUsername, setAdminUsername] = useState<string>('admin');
  const [adminPassword, setAdminPassword] = useState<string>('Admin@Campus2026');
  const [adminLoginError, setAdminLoginError] = useState<string | null>(null);

  // Modals for admin actions
  const [showAddStudentModal, setShowAddStudentModal] = useState<boolean>(false);
  const [newStudentUsn, setNewStudentUsn] = useState<string>('DEMO-USN-');
  const [newStudentId, setNewStudentId] = useState<string>('DEMO-');
  const [newStudentName, setNewStudentName] = useState<string>('');
  const [newStudentDept, setNewStudentDept] = useState<string>('Computer Science & Engineering');
  const [newStudentYear, setNewStudentYear] = useState<string>('3rd Year');
  const [newStudentQuota, setNewStudentQuota] = useState<number>(1024);
  const [newStudentTimeout, setNewStudentTimeout] = useState<number>(120);
  const [newStudentPassword, setNewStudentPassword] = useState<string>('StudentPass123!');

  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [editQuotaValue, setEditQuotaValue] = useState<number>(1024);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [operatingMac, setOperatingMac] = useState<string | null>(null);
  const [operatingStudentId, setOperatingStudentId] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);

  // Filters for student directory
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterBatch, setFilterBatch] = useState<string>('ALL');
  const [filterDept, setFilterDept] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const fetchAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [statusRes, telemetryRes, studentsRes, sessionsRes] = await Promise.all([
        api.getGatewayStatus().catch((err) => ({
          gateway_ip: '192.168.214.2',
          gateway_connected: false,
          opennds_running: false,
          active_clients_count: 0,
          error: err.response?.data?.detail || err.message || 'Gateway unreachable',
        })),
        api.getGatewayTelemetry().catch(() => null),
        api.getGatewayStudents().catch(() => []),
        api.getGatewaySessions().catch((err) => ({
          gateway_connected: false,
          active_clients_count: 0,
          live_clients: [],
          recent_history: [],
          error: err.response?.data?.detail || err.message,
        })),
      ]);

      setStatus(statusRes);
      setTelemetry(telemetryRes);
      setStudents(studentsRes);
      setLiveClients(sessionsRes.live_clients || []);
      setHistory(sessionsRes.recent_history || []);

      // If admin, also fetch event audit log
      if (adminAuth.isAuthenticated()) {
        try {
          const evts = await api.adminGetEvents(50);
          setEvents(evts);
        } catch {
          // Non-blocking if admin token expired
        }
      }
    } catch (err: any) {
      console.error('Failed to load gateway data:', err);
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Check admin session profile
  useEffect(() => {
    if (adminAuth.isAuthenticated()) {
      api.adminGetMe()
        .then((me) => setAdminUser(me))
        .catch(() => {
          adminAuth.clearToken();
          setIsAdmin(false);
        });
    }
  }, [isAdmin]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchAllData();
    }, 8000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAllData]);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdminLoginError(null);
    try {
      const res = await api.adminLogin({
        username: adminUsername.trim(),
        password: adminPassword,
      });
      setIsAdmin(true);
      setShowAdminModal(false);
      setActionMessage({
        type: 'success',
        text: `Administrator authenticated successfully as ${res.full_name} (${res.role}). Administrative controls unlocked.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setAdminLoginError(err.response?.data?.detail || 'Invalid administrator username or password.');
    }
  };

  const handleAdminLogout = async () => {
    await api.adminLogout();
    setIsAdmin(false);
    setAdminUser(null);
    setActionMessage({
      type: 'success',
      text: 'Administrator logged out. Sensitive endpoints locked.',
    });
  };

  const handleDeauth = async (mac: string) => {
    setOperatingMac(mac);
    setActionMessage(null);
    try {
      if (isAdmin) {
        await api.adminDeauthClient(mac);
      } else {
        await api.deauthClient(mac);
      }
      setActionMessage({
        type: 'success',
        text: `Client ${mac} has been disconnected and de-authenticated from OpenWrt gateway.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || `Failed to de-authenticate ${mac}`,
      });
    } finally {
      setOperatingMac(null);
    }
  };

  const handleResetQuota = async (studentId: string) => {
    setOperatingStudentId(studentId);
    setActionMessage(null);
    try {
      const updated = isAdmin
        ? await api.adminResetQuota(studentId)
        : await api.resetStudentQuota(studentId);
      setActionMessage({
        type: 'success',
        text: `Daily data usage reset to 0.0 MiB for ${updated.name} (${updated.student_id}). Full ${updated.daily_quota_mb} MiB quota restored.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || `Failed to reset quota for ${studentId}`,
      });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleToggleActive = async (student: Student) => {
    if (!isAdmin) {
      setShowAdminModal(true);
      return;
    }
    setOperatingStudentId(student.student_id);
    try {
      const updated = await api.adminUpdateStudent(student.student_id, {
        is_active: !student.is_active,
      });
      setActionMessage({
        type: 'success',
        text: `Student ${updated.name} account status updated to ${updated.is_active ? 'ACTIVE' : 'DISABLED'}.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update student status.',
      });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleSaveEditQuota = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;
    try {
      const updated = await api.adminUpdateStudent(editingStudent.student_id, {
        daily_quota_mb: Number(editQuotaValue),
      });
      setActionMessage({
        type: 'success',
        text: `Daily quota for ${updated.name} updated to ${updated.daily_quota_mb} MiB.`,
      });
      setEditingStudent(null);
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update student quota.',
      });
    }
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.adminCreateStudent({
        college_usn: newStudentUsn.trim(),
        student_id: newStudentId.trim(),
        name: newStudentName.trim(),
        department: newStudentDept,
        academic_year: newStudentYear,
        daily_quota_mb: Number(newStudentQuota),
        session_timeout_mins: Number(newStudentTimeout),
        password: newStudentPassword,
      });
      setActionMessage({
        type: 'success',
        text: `New student account created: ${created.name} (USN: ${created.college_usn}, Quota: ${created.daily_quota_mb} MiB).`,
      });
      setShowAddStudentModal(false);
      setNewStudentName('');
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to create student account.',
      });
    }
  };

  const handleApproveStudent = async (studentId: string) => {
    if (!isAdmin) {
      setShowAdminModal(true);
      return;
    }
    setOperatingStudentId(studentId);
    try {
      await api.adminSetApproval(studentId, 'APPROVED');
      setActionMessage({
        type: 'success',
        text: `Student ${studentId} approved for campus Wi-Fi access. Account is now active.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to approve student registration.',
      });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleRejectStudent = async (studentId: string) => {
    if (!isAdmin) {
      setShowAdminModal(true);
      return;
    }
    setOperatingStudentId(studentId);
    try {
      await api.adminSetApproval(studentId, 'REJECTED');
      setActionMessage({
        type: 'success',
        text: `Student registration ${studentId} rejected. Internet access remains blocked.`,
      });
      await fetchAllData();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to reject student registration.',
      });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const pendingStudents = students.filter(
    (s) => s.approval_status === 'PENDING_APPROVAL'
  );

  const filteredStudents = students.filter((s) => {
    if (filterBatch !== 'ALL' && String(s.batch_year) !== filterBatch) {
      return false;
    }
    if (filterDept !== 'ALL') {
      const code = s.department_code || (
        s.department.toLowerCase().includes('computer science') ? 'CS' :
        s.department.toLowerCase().includes('technology') ? 'CT' :
        s.department.toLowerCase().includes('information') ? 'IT' :
        s.department.toLowerCase().includes('electronics') ? 'EC' :
        s.department.toLowerCase().includes('mechanical') ? 'ME' : ''
      );
      if (code !== filterDept) return false;
    }
    if (filterStatus !== 'ALL') {
      const st = s.approval_status || (s.is_active ? 'APPROVED' : 'DISABLED');
      if (st !== filterStatus) return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchUsn = (s.college_usn || '').toLowerCase().includes(q);
      const matchId = (s.student_id || '').toLowerCase().includes(q);
      const matchName = (s.name || '').toLowerCase().includes(q);
      const matchDept = (s.department || '').toLowerCase().includes(q);
      if (!matchUsn && !matchId && !matchName && !matchDept) return false;
    }
    return true;
  });

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GiB`;
  };

  return (
    <div className="space-y-6">
      {/* Three-Tier Academic Distinction Banner */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live Gateway (OpenWrt)
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1">
              <Radio className="w-3 h-3" />
              Survey Measured (Laptop)
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Synthetic Simulation (RF Engine)
            </span>
          </div>
          <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
            Campus Gateway &amp; Student Quota Management
          </h1>
          <p className="text-xs text-slate-400">
            Enforced by OpenWrt 25.12.5 kernel netfilter (<code className="text-slate-300">nds_mangle</code> / <code className="text-slate-300">ndsctl</code>). Binary IEC Standard: <span className="text-emerald-400 font-semibold">1 GiB = 1,024 MiB</span>.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Admin Auth Indicator / Button */}
          {isAdmin ? (
            <div className="flex items-center gap-2 bg-slate-950/80 px-2.5 py-1.5 rounded-lg border border-indigo-500/40 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-indigo-300 font-semibold">Admin Mode</span>
              <button
                onClick={handleAdminLogout}
                className="text-slate-400 hover:text-rose-400 text-xs p-0.5 cursor-pointer"
                title="Log out of Administrator Mode"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAdminModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/30 text-xs font-semibold transition-all cursor-pointer"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Admin Login</span>
            </button>
          )}

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500 w-3.5 h-3.5"
            />
            <span>Auto-Poll (8s)</span>
          </label>

          <button
            onClick={fetchAllData}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => onNavigate('student-management')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 text-xs font-bold transition-all shadow-md shadow-emerald-600/30 cursor-pointer"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Student Portal</span>
          </button>
        </div>
      </div>

      {/* Action Notification Message */}
      {actionMessage && (
        <div
          className={`p-3 rounded-xl border flex items-center justify-between text-xs font-medium ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200'
              : 'bg-rose-950/40 border-rose-500/50 text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionMessage.text}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-slate-400 hover:text-slate-200 text-xs font-bold px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Gateway Hardware & Connectivity Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div
          className={`p-4 rounded-xl border transition-all ${
            status?.gateway_connected && status?.opennds_running
              ? 'bg-slate-900 border-emerald-500/40'
              : 'bg-rose-950/20 border-rose-500/40'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Gateway State</span>
            {status?.gateway_connected && status?.opennds_running ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/40">
                <CheckCircle2 className="w-3 h-3" /> Online
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/20 px-2 py-0.5 rounded-full border border-rose-500/40">
                <XCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <Server className="w-4 h-4 text-indigo-400" />
            OpenWrt {status?.opennds_version || '25.12.5'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Host: <span className="font-mono text-slate-300">{status?.gateway_ip || '192.168.214.2'}</span>
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">OpenNDS Daemon</span>
            <span className="text-[10px] font-semibold text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-500/30">
              Port 2050 / FAS
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Captive Engine
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Interface: <span className="font-mono text-slate-300">{status?.managed_interface || 'br-lan'}</span>
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Active Devices</span>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/30">
              Kernel Netfilter
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            {liveClients.length}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative <code className="text-slate-300">ndsctl json</code>
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Quota Standard</span>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/30">
              Binary IEC
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <HardDrive className="w-4 h-4 text-emerald-400" />
            1 GiB = 1,024 MiB
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Split Directional Caps (Up/Down)
          </p>
        </div>
      </div>

      {/* Tabs Switcher: Student Roster vs. Audit Events Log */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('roster')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'roster'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Student Accounts &amp; Quotas ({students.length})</span>
            {pendingStudents.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500 text-slate-950 font-extrabold animate-pulse">
                {pendingStudents.length} pending
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('events')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'events'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Security &amp; Quota Audit Log ({events.length})</span>
          </button>
        </div>

        {activeTab === 'roster' && (
          <div className="flex items-center gap-2">
            {isAdmin && (
              <button
                onClick={() => setShowAddStudentModal(true)}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-600/30 cursor-pointer flex items-center gap-1.5"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Add Student Account</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Live Active OpenNDS Clients Table */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Live Connected Client Devices on Gateway
            </h2>
            <p className="text-xs text-slate-400">
              Live hardware MACs and real-time netfilter byte counters reported by OpenNDS.
            </p>
          </div>
        </div>

        {liveClients.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Client Hardware MAC</th>
                  <th className="py-2.5 px-3">Assigned IP</th>
                  <th className="py-2.5 px-3">Authenticated Student</th>
                  <th className="py-2.5 px-3">Upload / Download Traffic</th>
                  <th className="py-2.5 px-3">Enforced Quota (Up / Down)</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {liveClients.map((client) => (
                  <tr key={client.mac} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-3">
                      <span className="font-mono text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40 font-semibold">
                        {client.mac}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">{client.ip || '192.168.214.x'}</td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-200">{client.student_name || 'Guest / Demo'}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{client.student_id || 'ID Unknown'}</div>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2 text-[11px]">
                        <span className="flex items-center text-slate-300 font-mono">
                          <ArrowUpRight className="w-3 h-3 text-cyan-400 mr-0.5" />
                          {formatBytes(client.upload_bytes)}
                        </span>
                        <span className="text-slate-600">/</span>
                        <span className="flex items-center text-slate-300 font-mono">
                          <ArrowDownRight className="w-3 h-3 text-indigo-400 mr-0.5" />
                          {formatBytes(client.download_bytes)}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300 text-[11px]">
                      {(client.upload_quota_kb / 1024).toFixed(1)} / {(client.download_quota_kb / 1024).toFixed(1)} MiB
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleDeauth(client.mac)}
                        disabled={operatingMac === client.mac}
                        className="px-2.5 py-1 rounded bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 text-[11px] font-bold transition-all cursor-pointer disabled:opacity-50"
                      >
                        {operatingMac === client.mac ? 'Disconnecting...' : 'Disconnect'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 rounded-lg bg-slate-950/60 border border-slate-800 text-center space-y-1.5">
            <p className="text-xs text-slate-300 font-semibold">No active student devices currently authenticated</p>
            <p className="text-[11px] text-slate-400 max-w-md mx-auto">
              OpenNDS is actively guarding the gateway interface. Use the Captive Portal to authenticate demo student accounts.
            </p>
          </div>
        )}
      </div>

      {/* Tab 1: Student Accounts & Daily Quotas Table */}
      {activeTab === 'roster' && (
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-0.5">
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-400" />
                Individual Student Accounts &amp; Quotas
              </h2>
              <p className="text-xs text-slate-400">
                Individual college USNs, departments, academic years, and binary IEC daily quotas (<span className="text-emerald-400 font-semibold">1 GiB = 1,024 MiB</span>).
              </p>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowAddStudentModal(true)}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-600/30 cursor-pointer flex items-center gap-1.5"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Add Student Account</span>
              </button>
            )}
          </div>

          {/* Pending Registrations Review Banner / Card */}
          {pendingStudents.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
                  <h3 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                    Pending Student Registrations ({pendingStudents.length} awaiting review)
                  </h3>
                </div>
                <span className="text-[11px] text-amber-400/80">
                  Self-registered via Captive Portal. Fail-closed: Zero internet until approved.
                </span>
              </div>

              <div className="overflow-x-auto rounded-lg border border-amber-500/30">
                <table className="w-full text-left text-xs">
                  <thead className="bg-amber-950/60 text-amber-300 border-b border-amber-500/30 uppercase text-[10px] tracking-wider font-semibold">
                    <tr>
                      <th className="py-2 px-3">College USN</th>
                      <th className="py-2 px-3">Student Name</th>
                      <th className="py-2 px-3">Department &amp; Batch</th>
                      <th className="py-2 px-3">Academic Year</th>
                      <th className="py-2 px-3">Status</th>
                      <th className="py-2 px-3 text-right">Administrative Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-amber-500/20 font-medium">
                    {pendingStudents.map((ps) => (
                      <tr key={ps.id} className="hover:bg-amber-950/40 transition-colors">
                        <td className="py-2.5 px-3">
                          <span className="font-mono font-bold text-amber-200 bg-amber-900/40 px-2 py-0.5 rounded border border-amber-700/50">
                            {ps.college_usn || ps.student_id}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-200 font-semibold">{ps.name}</td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {ps.department} {ps.batch_year ? `(Batch ${ps.batch_year})` : ''}
                        </td>
                        <td className="py-2.5 px-3 text-amber-300/90 font-mono text-[11px]">
                          {ps.academic_year || '—'}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                            Pending Approval
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleApproveStudent(ps.student_id)}
                              disabled={operatingStudentId === ps.student_id}
                              className="flex items-center gap-1 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow-sm transition-all cursor-pointer disabled:opacity-50"
                              title="Approve registration and activate account"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Approve</span>
                            </button>
                            <button
                              onClick={() => handleRejectStudent(ps.student_id)}
                              disabled={operatingStudentId === ps.student_id}
                              className="flex items-center gap-1 px-3 py-1 rounded bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 text-[11px] font-bold transition-all cursor-pointer disabled:opacity-50"
                              title="Reject student registration"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Filters Toolbar */}
          <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[280px]">
              {/* Search Box */}
              <div className="relative flex-1 min-w-[180px] max-w-xs">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search USN, name, dept..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white text-xs"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Batch Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Batch:</span>
                <select
                  value={filterBatch}
                  onChange={(e) => setFilterBatch(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="ALL">All Batches</option>
                  <option value="2022">2022</option>
                  <option value="2023">2023</option>
                  <option value="2024">2024</option>
                  <option value="2025">2025</option>
                  <option value="2026">2026</option>
                </select>
              </div>

              {/* Department Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Branch:</span>
                <select
                  value={filterDept}
                  onChange={(e) => setFilterDept(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="ALL">All Branches</option>
                  <option value="CS">CS (Computer Science)</option>
                  <option value="CT">CT (Computer Technology)</option>
                  <option value="IT">IT (Information Tech)</option>
                  <option value="EC">EC (Electronics)</option>
                  <option value="ME">ME (Mechanical)</option>
                </select>
              </div>

              {/* Approval Status Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Status:</span>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="APPROVED">Approved &amp; Active</option>
                  <option value="PENDING_APPROVAL">Pending Review</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="DISABLED">Disabled</option>
                </select>
              </div>

              {(searchQuery || filterBatch !== 'ALL' || filterDept !== 'ALL' || filterStatus !== 'ALL') && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setFilterBatch('ALL');
                    setFilterDept('ALL');
                    setFilterStatus('ALL');
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 text-[11px] font-semibold transition-all cursor-pointer"
                >
                  Reset Filters
                </button>
              )}
            </div>

            <div className="text-[11px] text-slate-400 font-medium">
              Showing <span className="text-slate-200 font-bold">{filteredStudents.length}</span> of {students.length} accounts
            </div>
          </div>

          {filteredStudents.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">College USN</th>
                    <th className="py-2.5 px-3">Student Name</th>
                    <th className="py-2.5 px-3">Department &amp; Year</th>
                    <th className="py-2.5 px-3">Daily Quota</th>
                    <th className="py-2.5 px-3">Usage &amp; Remaining</th>
                    <th className="py-2.5 px-3">Session Limit</th>
                    <th className="py-2.5 px-3">Approval Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {filteredStudents.map((student) => {
                    const used = student.used_quota_mb;
                    const total = student.daily_quota_mb;
                    const remaining = student.remaining_quota_mb;
                    const percentUsed = Math.min(100, Math.round((used / total) * 100));
                    const isExhausted = remaining <= 0;
                    const approvalSt = student.approval_status || (student.is_active ? 'APPROVED' : 'DISABLED');

                    return (
                      <tr key={student.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono font-bold text-emerald-300 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/30">
                              {student.college_usn || student.student_id}
                            </span>
                            {student.is_demo ? (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold uppercase bg-cyan-950/80 text-cyan-300 border border-cyan-800/40">
                                Demo
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold uppercase bg-indigo-950/80 text-indigo-300 border border-indigo-800/40">
                                Student
                              </span>
                            )}
                          </div>
                          {student.college_usn && student.college_usn !== student.student_id && (
                            <div className="text-[10px] text-slate-400 font-mono mt-0.5">{student.student_id}</div>
                          )}
                        </td>
                        <td className="py-3 px-3 text-slate-200 font-semibold">{student.name}</td>
                        <td className="py-3 px-3 text-slate-400">
                          <div>{student.department}</div>
                          <div className="text-[10px] text-indigo-400 font-medium">
                            {student.batch_year ? `Batch ${student.batch_year} · ` : ''}{student.academic_year || '3rd Year'}
                          </div>
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-300">
                          {student.daily_quota_mb} MiB ({student.daily_quota_mb >= 1024 ? `${(student.daily_quota_mb / 1024).toFixed(1)} GiB` : ''})
                        </td>
                        <td className="py-3 px-3 min-w-[180px]">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className={isExhausted ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                                {used.toFixed(1)} / {total} MiB ({percentUsed}%)
                              </span>
                              <span className={isExhausted ? 'text-rose-400 font-bold' : 'text-emerald-400 font-medium'}>
                                {remaining.toFixed(1)} MiB rem.
                              </span>
                            </div>
                            <div className="w-full h-1.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  isExhausted ? 'bg-rose-500' : percentUsed > 75 ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${percentUsed}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-slate-400 font-mono">{student.session_timeout_mins}m</td>
                        <td className="py-3 px-3">
                          {approvalSt === 'APPROVED' && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Approved
                            </span>
                          )}
                          {approvalSt === 'PENDING_APPROVAL' && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                              Pending Review
                            </span>
                          )}
                          {approvalSt === 'REJECTED' && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              Rejected
                            </span>
                          )}
                          {approvalSt === 'DISABLED' && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-800 text-slate-400 border border-slate-700">
                              Disabled
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Quick Approval / Rejection buttons if pending */}
                            {approvalSt === 'PENDING_APPROVAL' && (
                              <>
                                <button
                                  onClick={() => handleApproveStudent(student.student_id)}
                                  disabled={operatingStudentId === student.student_id}
                                  className="p-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 transition-all cursor-pointer"
                                  title="Approve Student Account"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => handleRejectStudent(student.student_id)}
                                  disabled={operatingStudentId === student.student_id}
                                  className="p-1 rounded bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 transition-all cursor-pointer"
                                  title="Reject Student Registration"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </>
                            )}

                            {/* Quick Re-approve if rejected */}
                            {approvalSt === 'REJECTED' && (
                              <button
                                onClick={() => handleApproveStudent(student.student_id)}
                                disabled={operatingStudentId === student.student_id}
                                className="px-2 py-0.5 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold transition-all cursor-pointer"
                                title="Re-approve Student Account"
                              >
                                Re-approve
                              </button>
                            )}

                            {isAdmin && (
                              <>
                                <button
                                  onClick={() => {
                                    setEditingStudent(student);
                                    setEditQuotaValue(student.daily_quota_mb);
                                  }}
                                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 transition-all cursor-pointer"
                                  title="Change Quota"
                                >
                                  <Edit className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => handleToggleActive(student)}
                                  className={`p-1 rounded transition-all cursor-pointer ${
                                    student.is_active
                                      ? 'bg-slate-800 hover:bg-rose-950/60 text-slate-400 hover:text-rose-300'
                                      : 'bg-emerald-950/60 text-emerald-300 hover:bg-emerald-900/60'
                                  }`}
                                  title={student.is_active ? 'Disable Account' : 'Reactivate Account'}
                                >
                                  <Power className="w-3.5 h-3.5" />
                                </button>
                              </>
                            )}
                            <button
                              onClick={() => handleResetQuota(student.student_id)}
                              disabled={operatingStudentId === student.student_id}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold transition-all cursor-pointer border border-slate-700 disabled:opacity-50"
                              title="Reset consumed data to 0 MiB"
                            >
                              Reset
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 rounded-lg bg-slate-950/60 border border-slate-800 text-center space-y-2">
              <Users className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-xs text-slate-300 font-semibold">No student accounts found</p>
              <p className="text-[11px] text-slate-500">
                No student accounts match your active filters. Try adjusting your batch, department, or search query.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Security & Quota Audit Events Log */}
      {activeTab === 'events' && (
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                Immutable Security &amp; Quota Audit Ledger
              </h2>
              <p className="text-xs text-slate-400">
                Chronological record of authentications, quota cutoffs, resets, and administrative overrides.
              </p>
            </div>
            {!isAdmin && (
              <span className="text-xs text-amber-400 flex items-center gap-1">
                <Lock className="w-3.5 h-3.5" />
                Log in as administrator to unlock live audit feed
              </span>
            )}
          </div>

          {events.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Timestamp (UTC)</th>
                    <th className="py-2.5 px-3">Event Type</th>
                    <th className="py-2.5 px-3">Student USN / Identifier</th>
                    <th className="py-2.5 px-3">Hardware MAC</th>
                    <th className="py-2.5 px-3">Actor</th>
                    <th className="py-2.5 px-3">Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {events.map((evt) => (
                    <tr key={evt.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">
                        {new Date(evt.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                            evt.event_type.includes('SUCCESS')
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                              : evt.event_type.includes('EXHAUSTED') || evt.event_type.includes('FAILED')
                              ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                              : evt.event_type.includes('DEAUTH')
                              ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                              : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                          }`}
                        >
                          {evt.event_type}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">{evt.student_id || '—'}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{evt.client_mac || '—'}</td>
                      <td className="py-2.5 px-3 text-slate-400 text-[11px] font-semibold">{evt.actor}</td>
                      <td className="py-2.5 px-3 text-slate-300 text-[11px] max-w-md truncate">{evt.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 rounded-lg bg-slate-950/60 border border-slate-800 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-xs text-slate-400">
                {isAdmin ? 'No security events recorded yet.' : 'Administrator authorization required to view ledger.'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Admin Login Modal */}
      {showAdminModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                <Lock className="w-4 h-4" />
                <span>Administrator Authentication</span>
              </div>
              <button onClick={() => setShowAdminModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleAdminLogin} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Admin Username</label>
                <input
                  type="text"
                  required
                  value={adminUsername}
                  onChange={(e) => setAdminUsername(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Admin Password</label>
                <input
                  type="password"
                  required
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">Default demo: <code className="text-slate-400">admin / Admin@Campus2026</code></p>
              </div>

              {adminLoginError && (
                <div className="p-2 rounded bg-rose-950/50 border border-rose-800 text-[11px] text-rose-300">
                  {adminLoginError}
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAdminModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30"
                >
                  Authenticate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Student Modal */}
      {showAddStudentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <UserPlus className="w-4 h-4" />
                <span>Add College Student Account</span>
              </div>
              <button onClick={() => setShowAddStudentModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleCreateStudent} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">College USN</label>
                  <input
                    type="text"
                    required
                    value={newStudentUsn}
                    onChange={(e) => setNewStudentUsn(e.target.value)}
                    placeholder="DEMO-USN-01"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Roll Number / ID</label>
                  <input
                    type="text"
                    required
                    value={newStudentId}
                    onChange={(e) => setNewStudentId(e.target.value)}
                    placeholder="DEMO-CSE-09"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Student Full Name</label>
                <input
                  type="text"
                  required
                  value={newStudentName}
                  onChange={(e) => setNewStudentName(e.target.value)}
                  placeholder="e.g. John Doe (Demo)"
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Department</label>
                  <select
                    value={newStudentDept}
                    onChange={(e) => setNewStudentDept(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200"
                  >
                    <option value="Computer Science & Engineering">CSE</option>
                    <option value="Information Technology">IT</option>
                    <option value="Electronics & Communication">ECE</option>
                    <option value="Mechanical Engineering">Mech</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Academic Year</label>
                  <select
                    value={newStudentYear}
                    onChange={(e) => setNewStudentYear(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200"
                  >
                    <option value="1st Year">1st Year</option>
                    <option value="2nd Year">2nd Year</option>
                    <option value="3rd Year">3rd Year</option>
                    <option value="4th Year">4th Year</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Daily Quota (MiB)</label>
                  <input
                    type="number"
                    min="128"
                    step="128"
                    required
                    value={newStudentQuota}
                    onChange={(e) => setNewStudentQuota(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono"
                  />
                  <span className="text-[10px] text-slate-500">1024 MiB = 1 GiB</span>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Session Limit (mins)</label>
                  <input
                    type="number"
                    min="15"
                    required
                    value={newStudentTimeout}
                    onChange={(e) => setNewStudentTimeout(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={newStudentPassword}
                  onChange={(e) => setNewStudentPassword(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddStudentModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold"
                >
                  Create Student
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Quota Modal */}
      {editingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                <Edit className="w-4 h-4" />
                <span>Adjust Daily Quota</span>
              </div>
              <button onClick={() => setEditingStudent(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSaveEditQuota} className="space-y-3">
              <p className="text-xs text-slate-300">
                Updating quota for <span className="font-bold text-white">{editingStudent.name}</span> ({editingStudent.college_usn || editingStudent.student_id}):
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">New Daily Quota (MiB)</label>
                <input
                  type="number"
                  min="64"
                  step="128"
                  required
                  value={editQuotaValue}
                  onChange={(e) => setEditQuotaValue(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono"
                />
                <p className="text-[10px] text-slate-500 mt-1">1024 MiB = 1 GiB &bull; 2048 MiB = 2 GiB</p>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingStudent(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold"
                >
                  Save Quota
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
