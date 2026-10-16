import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Users,
  Search,
  Filter,
  UserPlus,
  Check,
  X,
  Edit,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  HardDrive,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { api, adminAuth } from '../api/client';
import { Student } from '../types';

export const StudentManagement: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [operatingStudentId, setOperatingStudentId] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterBatch, setFilterBatch] = useState<string>('ALL');
  const [filterDept, setFilterDept] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [accountTypeTab, setAccountTypeTab] = useState<'ORDINARY' | 'DEMO_TESTING' | 'ALL'>('ORDINARY');

  // Add Student Modal State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newUsn, setNewUsn] = useState<string>('ENG24CS0101');
  const [newName, setNewName] = useState<string>('');
  const [newEmail, setNewEmail] = useState<string>('');
  const [newDept, setNewDept] = useState<string>('Computer Science Core');
  const [newBatch, setNewBatch] = useState<number>(2024);
  const [newYear, setNewYear] = useState<string>('3rd Year');
  const [newQuota, setNewQuota] = useState<number>(1024);
  const [newTimeout, setNewTimeout] = useState<number>(120);
  const [newPassword, setNewPassword] = useState<string>('StudentPass123!');
  const [isSubmittingNew, setIsSubmittingNew] = useState<boolean>(false);

  // Edit Quota Modal State
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [editQuotaMb, setEditQuotaMb] = useState<number>(1024);
  const [editTimeoutMins, setEditTimeoutMins] = useState<number>(120);
  const [isSavingEdit, setIsSavingEdit] = useState<boolean>(false);

  const fetchStudents = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await api.getGatewayStudents();
      setStudents(data);
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: 'Failed to retrieve students: ' + (err.message || 'Network error'),
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  // Designated demo account detection (only DEMO-CSE-01 is designated to appear in normal roster)
  const isDesignatedDemo = useCallback((s: Student) => {
    return Boolean(
      s.is_demo && (
        s.is_designated_demo ||
        s.student_id === 'DEMO-CSE-01' ||
        s.college_usn === 'DEMO-USN-CSE01'
      )
    );
  }, []);

  // Derived student categories
  const pendingStudents = useMemo(() => {
    return students.filter((s) => s.approval_status === 'PENDING_APPROVAL');
  }, [students]);

  const ordinaryStudents = useMemo(() => {
    return students.filter((s) => !s.is_demo || isDesignatedDemo(s));
  }, [students, isDesignatedDemo]);

  const demoFixtures = useMemo(() => {
    return students.filter((s) => s.is_demo);
  }, [students]);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      // Type Tab filter:
      // ORDINARY: Genuine students + at most ONE designated demo account (DEMO-CSE-01)
      if (accountTypeTab === 'ORDINARY') {
        if (s.is_demo && !isDesignatedDemo(s)) return false;
      }
      // DEMO_TESTING: All demo accounts accessible for testing
      else if (accountTypeTab === 'DEMO_TESTING') {
        if (!s.is_demo) return false;
      }

      // Status filter
      if (filterStatus !== 'ALL' && s.approval_status !== filterStatus) return false;

      // Batch filter
      if (filterBatch !== 'ALL' && s.batch_year?.toString() !== filterBatch) return false;

      // Department filter
      if (filterDept !== 'ALL') {
        const d = (s.department_code || s.department || '').toUpperCase();
        if (!d.includes(filterDept)) return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesUsn = (s.college_usn || '').toLowerCase().includes(q);
        const matchesId = (s.student_id || '').toLowerCase().includes(q);
        const matchesName = (s.name || '').toLowerCase().includes(q);
        const matchesEmail = (s.email || '').toLowerCase().includes(q);
        const matchesDept = (s.department || '').toLowerCase().includes(q);
        if (!matchesUsn && !matchesId && !matchesName && !matchesEmail && !matchesDept) return false;
      }

      return true;
    });
  }, [students, accountTypeTab, filterStatus, filterBatch, filterDept, searchQuery, isDesignatedDemo]);

  // Actions
  const handleApprove = async (studentId: string) => {
    setOperatingStudentId(studentId);
    setActionMessage(null);
    try {
      await api.adminSetApproval(studentId, 'APPROVED', 'Approved by administrator');
      setActionMessage({ type: 'success', text: `Student ${studentId} approved and activated successfully.` });
      await fetchStudents();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Approval failed' });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleReject = async (studentId: string) => {
    setOperatingStudentId(studentId);
    setActionMessage(null);
    try {
      await api.adminSetApproval(studentId, 'REJECTED', 'Rejected by administrator');
      setActionMessage({ type: 'success', text: `Student ${studentId} registration rejected.` });
      await fetchStudents();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Rejection failed' });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleResetQuota = async (studentId: string) => {
    if (!window.confirm(`Reset consumed quota to 0.0 MiB for student ${studentId}?`)) return;
    setOperatingStudentId(studentId);
    setActionMessage(null);
    try {
      await api.adminResetQuota(studentId);
      setActionMessage({ type: 'success', text: `Daily quota usage reset to 0.0 MiB for ${studentId}.` });
      await fetchStudents();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Quota reset failed' });
    } finally {
      setOperatingStudentId(null);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;
    setIsSavingEdit(true);
    try {
      await api.adminUpdateStudent(editingStudent.student_id, {
        daily_quota_mb: editQuotaMb,
        session_timeout_mins: editTimeoutMins,
      });
      setActionMessage({ type: 'success', text: `Quota updated to ${editQuotaMb} MiB for ${editingStudent.student_id}.` });
      setEditingStudent(null);
      await fetchStudents();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Failed to update quota' });
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingNew(true);
    try {
      await api.adminCreateStudent({
        student_id: newUsn.trim(),
        college_usn: newUsn.trim(),
        name: newName.trim(),
        department: newDept,
        academic_year: newYear,
        password: newPassword,
        daily_quota_mb: newQuota,
        session_timeout_mins: newTimeout,
        ...(newEmail.trim() ? { email: newEmail.trim() } : {}),
      } as any);
      setActionMessage({ type: 'success', text: `Account created for ${newUsn}.` });
      setShowAddModal(false);
      setNewName('');
      setNewEmail('');
      await fetchStudents();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Account creation failed' });
    } finally {
      setIsSubmittingNew(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
            <Users className="w-4 h-4" />
            <span>Student Authentication &amp; Quota Ledger</span>
          </div>
          <h1 className="text-xl font-extrabold text-white tracking-tight">Student Management</h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Review self-registrations, enforce binary IEC daily bandwidth limits (1 GiB = 1,024 MiB), and manage active student directory records.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchStudents}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-all cursor-pointer"
            title="Refresh student roster"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 transition-all cursor-pointer"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Add Student Account</span>
          </button>
        </div>
      </div>

      {/* Action Notification Message */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs animate-in fade-in ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
              : 'bg-rose-950/40 border-rose-500/40 text-rose-200'
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
            className="text-slate-400 hover:text-white text-xs px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Pending Approvals Alert Banner */}
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
              Fail-closed security: Devices have zero internet access until approved.
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-amber-500/30">
            <table className="w-full text-left text-xs">
              <thead className="bg-amber-950/60 text-amber-300 border-b border-amber-500/30 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="py-2.5 px-3">College USN</th>
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Department &amp; Batch</th>
                  <th className="py-2.5 px-3">Academic Year</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Administrative Action</th>
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
                          onClick={() => handleApprove(ps.student_id)}
                          disabled={operatingStudentId === ps.student_id}
                          className="flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow-sm transition-all cursor-pointer disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => handleReject(ps.student_id)}
                          disabled={operatingStudentId === ps.student_id}
                          className="flex items-center gap-1 px-3 py-1 rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 text-[11px] font-bold transition-all cursor-pointer disabled:opacity-50"
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

      {/* Account Type Tabs & Filter Toolbar */}
      <div className="space-y-3">
        {/* Roster Mode Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-2">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setAccountTypeTab('ORDINARY')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                accountTypeTab === 'ORDINARY'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span>Active Roster (Normal List)</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${accountTypeTab === 'ORDINARY' ? 'bg-indigo-900/80 text-white' : 'bg-slate-800 text-slate-400'}`}>
                {ordinaryStudents.length}
              </span>
            </button>
            <button
              onClick={() => setAccountTypeTab('DEMO_TESTING')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                accountTypeTab === 'DEMO_TESTING'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span>Demo &amp; Testing Fixtures</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${accountTypeTab === 'DEMO_TESTING' ? 'bg-cyan-900/80 text-white' : 'bg-slate-800 text-slate-400'}`}>
                {demoFixtures.length}
              </span>
            </button>
            <button
              onClick={() => setAccountTypeTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                accountTypeTab === 'ALL'
                  ? 'bg-slate-700 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span>All Records (Audit)</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${accountTypeTab === 'ALL' ? 'bg-slate-900 text-slate-200' : 'bg-slate-800 text-slate-400'}`}>
                {students.length}
              </span>
            </button>
          </div>

          <span className="text-xs text-slate-400">
            Showing <strong className="text-white">{filteredStudents.length}</strong> accounts
          </span>
        </div>

        {/* Informative Roster Scope Banner */}
        {accountTypeTab === 'ORDINARY' && (
          <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-[11px] text-indigo-300 flex items-center justify-between">
            <span>
              <strong>Normal Student Directory:</strong> Displays enrolled real students and at most <strong>one designated demo account</strong> (DEMO-CSE-01) for standard viva demonstration. Remaining testing fixtures are safely isolated under the <em>Demo &amp; Testing Fixtures</em> tab.
            </span>
          </div>
        )}
        {accountTypeTab === 'DEMO_TESTING' && (
          <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-500/20 text-[11px] text-cyan-300 flex items-center justify-between">
            <span>
              <strong>Demo &amp; Testing Fixtures Section:</strong> All 5 pre-seeded testing fixtures (Primary 1 GiB, 2 GiB High, 512 MiB Med, 256 MiB Low, and 100% Exhaustion block test) are accessible here for authorized testing without cluttering normal student records.
            </span>
          </div>
        )}

        {/* Search & Filter Bar */}
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[280px]">
            {/* Search Box */}
            <div className="relative flex-1 min-w-[180px] max-w-xs">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search USN, name, dept..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
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
                className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
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
                className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="ALL">All Branches</option>
                <option value="CS">CS (Computer Science)</option>
                <option value="CT">CT (Computer Technology)</option>
                <option value="IT">IT (Information Tech)</option>
                <option value="EC">EC (Electronics)</option>
                <option value="ME">ME (Mechanical)</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-400">Status:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
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
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 text-[11px] font-semibold transition-all cursor-pointer"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Student Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        {filteredStudents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">College USN</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Daily Quota</th>
                  <th className="py-3 px-4">Used</th>
                  <th className="py-3 px-4">Remaining</th>
                  <th className="py-3 px-4">Approval Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
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
                      {/* 1. College USN */}
                      <td className="py-3.5 px-4">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="font-mono font-bold text-emerald-300 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/30">
                            {student.college_usn || student.student_id}
                          </span>
                          {student.is_demo ? (
                            isDesignatedDemo(student) ? (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-emerald-950/80 text-emerald-300 border border-emerald-700/50" title="Designated primary demonstration account">
                                Primary Demo
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-cyan-950/80 text-cyan-300 border border-cyan-800/40">
                                Testing Fixture
                              </span>
                            )
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">
                              Enrolled
                            </span>
                          )}
                          {student.student_id === 'DEMO-EXHAUSTED' && (
                            <span className="px-1 py-0.5 rounded text-[8px] font-bold uppercase bg-rose-950/90 text-rose-300 border border-rose-800/50">
                              Cutoff Test
                            </span>
                          )}
                        </div>
                      </td>

                      {/* 2. Student Name & Email */}
                      <td className="py-3.5 px-4">
                        <div className="text-slate-200 font-semibold">{student.name}</div>
                        {student.email && (
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5">{student.email}</div>
                        )}
                      </td>

                      {/* 3. Department */}
                      <td className="py-3.5 px-4 text-slate-400">
                        <div className="text-slate-300 font-medium">{student.department}</div>
                        <div className="text-[10px] text-indigo-400 font-medium">
                          {student.batch_year ? `Batch ${student.batch_year} · ` : ''}{student.academic_year || '3rd Year'}
                        </div>
                      </td>

                      {/* 4. Daily Quota */}
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {student.daily_quota_mb >= 1024
                          ? `${(student.daily_quota_mb / 1024).toFixed(1)} GiB (${student.daily_quota_mb} MiB)`
                          : `${student.daily_quota_mb} MiB`}
                      </td>

                      {/* 5. Used */}
                      <td className="py-3.5 px-4 font-mono">
                        <span className={isExhausted ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                          {used.toFixed(1)} MiB ({percentUsed}%)
                        </span>
                      </td>

                      {/* 6. Remaining */}
                      <td className="py-3.5 px-4 min-w-[150px]">
                        <div className="space-y-1">
                          <span className={`font-mono text-xs font-semibold ${isExhausted ? 'text-rose-400 font-bold' : 'text-emerald-400'}`}>
                            {remaining.toFixed(1)} MiB
                          </span>
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

                      {/* 7. Approval Status */}
                      <td className="py-3.5 px-4">
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

                      {/* 8. Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {approvalSt === 'PENDING_APPROVAL' && (
                            <>
                              <button
                                onClick={() => handleApprove(student.student_id)}
                                disabled={operatingStudentId === student.student_id}
                                className="p-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 transition-all cursor-pointer"
                                title="Approve Student Account"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleReject(student.student_id)}
                                disabled={operatingStudentId === student.student_id}
                                className="p-1.5 rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 transition-all cursor-pointer"
                                title="Reject Student Registration"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}

                          <button
                            onClick={() => {
                              setEditingStudent(student);
                              setEditQuotaMb(student.daily_quota_mb);
                              setEditTimeoutMins(student.session_timeout_mins);
                            }}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 transition-all cursor-pointer"
                            title="Edit Daily Quota Allowance"
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleResetQuota(student.student_id)}
                            disabled={operatingStudentId === student.student_id}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 transition-all cursor-pointer"
                            title="Reset Quota Consumption to 0 MiB"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
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
          <div className="p-8 text-center text-xs text-slate-400 space-y-1">
            <p className="font-semibold text-slate-300">No student records found matching the active filters.</p>
            <p>Try resetting the search query or changing the branch/batch dropdowns.</p>
          </div>
        )}
      </div>

      {/* Edit Quota Modal */}
      {editingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-indigo-400" />
                <span>Adjust Quota: {editingStudent.college_usn || editingStudent.student_id}</span>
              </h3>
              <button
                onClick={() => setEditingStudent(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-slate-300">Daily Quota Limit (MiB)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={editQuotaMb}
                    onChange={(e) => setEditQuotaMb(Number(e.target.value))}
                    min={64}
                    max={10240}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                    required
                  />
                  <span className="text-slate-400 font-mono">
                    ({(editQuotaMb / 1024).toFixed(1)} GiB)
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-300">Session Window Timeout (Minutes)</label>
                <input
                  type="number"
                  value={editTimeoutMins}
                  onChange={(e) => setEditTimeoutMins(Number(e.target.value))}
                  min={15}
                  max={480}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingStudent(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingEdit}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-md shadow-indigo-600/30 disabled:opacity-50"
                >
                  {isSavingEdit ? 'Saving...' : 'Save Allowance'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Student Account Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-emerald-400" />
                <span>Provision New Student Account</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateStudent} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">College USN</label>
                  <input
                    type="text"
                    value={newUsn}
                    onChange={(e) => setNewUsn(e.target.value.toUpperCase())}
                    placeholder="ENG24CS0101"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">Full Name</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Student Name"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-300 flex items-center justify-between">
                  <span>College Email</span>
                  <span className="text-[10px] text-slate-500 font-normal">Optional (for password reset)</span>
                </label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="e.g. student@college.edu.in"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">Department</label>
                  <select
                    value={newDept}
                    onChange={(e) => setNewDept(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  >
                    <option value="Computer Science Core">Computer Science Core</option>
                    <option value="Computer Technology">Computer Technology</option>
                    <option value="Information Technology">Information Technology</option>
                    <option value="Electronics & Communication">Electronics &amp; Communication</option>
                    <option value="Mechanical Engineering">Mechanical Engineering</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">Batch Year</label>
                  <input
                    type="number"
                    value={newBatch}
                    onChange={(e) => setNewBatch(Number(e.target.value))}
                    min={2020}
                    max={2030}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">Daily Quota (MiB)</label>
                  <input
                    type="number"
                    value={newQuota}
                    onChange={(e) => setNewQuota(Number(e.target.value))}
                    min={128}
                    max={10240}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-300">Default Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                    required
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingNew}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-md shadow-emerald-600/30 disabled:opacity-50"
                >
                  {isSubmittingNew ? 'Creating...' : 'Provision Student'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
