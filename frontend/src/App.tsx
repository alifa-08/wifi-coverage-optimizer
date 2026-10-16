import React, { useState, useEffect } from 'react';
import { api, adminAuth } from './api/client';
import {
  Building,
  Floor,
  DashboardSummary,
  DeadZone,
  PredictionGridPoint,
  APRecommendation,
  BeforeAfterComparison,
  Alert,
  MLModelMetrics,
  Measurement,
  DeadZoneAnalyticsSummary,
  StudentLoginResponse,
} from './types';
import { Navbar } from './components/Navbar';
import { Sidebar, PageId } from './components/Sidebar';

// Dedicated Landing & Portal Pages
import { WelcomeLanding } from './pages/WelcomeLanding';
import { StudentLogin } from './pages/StudentLogin';
import { StudentRegister } from './pages/StudentRegister';
import { StudentDashboard } from './pages/StudentDashboard';
import { ForgotPassword } from './pages/ForgotPassword';
import { ResetPassword } from './pages/ResetPassword';
import { AdminLogin } from './pages/AdminLogin';

// Admin 11 Core Modules
import { Dashboard } from './pages/Dashboard';
import { StudentManagement } from './pages/StudentManagement';
import { GatewayQuotas } from './pages/GatewayQuotas';
import { CoverageMap } from './pages/CoverageMap';
import { DeadZonePrediction } from './pages/DeadZonePrediction';
import { APOptimization } from './pages/APOptimization';
import { BeforeAfter } from './pages/BeforeAfter';
import { NetworkAnalytics } from './pages/NetworkAnalytics';
import { Alerts } from './pages/Alerts';
import { SimulationControl } from './pages/SimulationControl';
import { SystemDiagnostics } from './pages/SystemDiagnostics';

export type ViewMode =
  | 'welcome'
  | 'student-login'
  | 'student-register'
  | 'student-forgot-password'
  | 'student-reset-password'
  | 'student-dashboard'
  | 'admin-login'
  | 'admin';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('welcome');
  const [resetToken, setResetToken] = useState<string>('');
  const [studentSession, setStudentSession] = useState<{
    response: StudentLoginResponse;
    collegeUsn: string;
  } | null>(null);

  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [floorId, setFloorId] = useState<number>(1);
  const [floor, setFloor] = useState<Floor | null>(null);
  const [buildings, setBuildings] = useState<Building[]>([]);

  // System Pipeline States
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [analytics, setAnalytics] = useState<DeadZoneAnalyticsSummary | null>(null);
  const [deadZones, setDeadZones] = useState<DeadZone[]>([]);
  const [selectedDeadZone, setSelectedDeadZone] = useState<DeadZone | null>(null);
  const [predictedGrid, setPredictedGrid] = useState<PredictionGridPoint[]>([]);
  const [recommendations, setRecommendations] = useState<APRecommendation[]>([]);
  const [comparison, setComparison] = useState<BeforeAfterComparison | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [mlMetrics, setMLMetrics] = useState<MLModelMetrics | null>(null);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);

  // Loading flags
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [isRunningBeforeAfter, setIsRunningBeforeAfter] = useState<boolean>(false);

  // Load all data for floor and run
  const refreshAllData = async (targetFloorId: number = floorId) => {
    try {
      const floorData = await api.getFloor(targetFloorId);
      setFloor(floorData);

      const summaryData = await api.getDashboardSummary(targetFloorId);
      setSummary(summaryData);
      setDeadZones(summaryData.dead_zones || []);

      const analyticsData = await api.getDeadZoneAnalytics(targetFloorId);
      setAnalytics(analyticsData);

      const alertsData = await api.getAlerts();
      setAlerts(alertsData);

      const metricsData = await api.getMLMetrics();
      setMLMetrics(metricsData);

      if (summaryData.run_id) {
        const [meas, preds, recs] = await Promise.all([
          api.getRunMeasurements(summaryData.run_id),
          api.getGridPredictions(summaryData.run_id),
          api.getRecommendations(targetFloorId, summaryData.run_id),
        ]);
        setMeasurements(meas);
        setPredictedGrid(preds);
        setRecommendations(recs);
      }
    } catch (err) {
      console.error('Error refreshing system data:', err);
    }
  };

  // Initial mount: load campus floorplan & verify simulation baseline
  useEffect(() => {
    const initializeSystem = async () => {
      setIsInitializing(true);
      try {
        const building = await api.getDefaultBuilding();
        setBuildings([building]);
        const firstFloor = building.floors[0];
        if (firstFloor) {
          setFloorId(firstFloor.id);
          setFloor(firstFloor);

          // Check if data exists; if not, auto-generate demo baseline
          const sum = await api.getDashboardSummary(firstFloor.id);
          if (!sum.has_data) {
            await api.generateDemo('Laboratory Dead Zone');
          }
          await refreshAllData(firstFloor.id);
        }
      } catch (err) {
        console.error('Failed to initialize campus environment:', err);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeSystem();
  }, []);

  // Check URL query parameters for reset tokens on initial load
  useEffect(() => {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token') || urlParams.get('reset_token');
      if (token) {
        setResetToken(token);
        setViewMode('student-reset-password');
      }
    } catch {
      // Ignore URL parsing issues
    }
  }, []);

  const handleRunBeforeAfter = async () => {
    if (!summary?.run_id) return;
    setIsRunningBeforeAfter(true);
    try {
      const comp = await api.runBeforeAfter(floorId, summary.run_id);
      setComparison(comp);
      setCurrentPage('before-after');
    } catch (err) {
      console.error('Before vs After simulation failed:', err);
    } finally {
      setIsRunningBeforeAfter(false);
    }
  };

  const handleResolveAlert = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      const updatedAlerts = await api.getAlerts();
      setAlerts(updatedAlerts);
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-200 space-y-4 font-sans">
        <div className="w-12 h-12 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
        <p className="text-sm font-semibold tracking-wide">
          Initializing Academic Block &amp; Wi-Fi Simulation Engine...
        </p>
      </div>
    );
  }

  // Handle Admin Exit / Logout (clears admin session token)
  const handleExitAdmin = () => {
    adminAuth.clearToken();
    setViewMode('welcome');
  };

  // 1. Role Separation: Welcome Landing Screen
  if (viewMode === 'welcome') {
    return (
      <WelcomeLanding
        onSelectStudentLogin={() => setViewMode('student-login')}
        onSelectStudentRegister={() => setViewMode('student-register')}
        onSelectAdminLogin={() => {
          if (adminAuth.isAuthenticated()) {
            setViewMode('admin');
            setCurrentPage('dashboard');
          } else {
            setViewMode('admin-login');
          }
        }}
      />
    );
  }

  // 2. Role Separation: Dedicated Student Login Form
  if (viewMode === 'student-login') {
    return (
      <StudentLogin
        onBackToWelcome={() => setViewMode('welcome')}
        onGoToRegister={() => setViewMode('student-register')}
        onGoToForgotPassword={() => setViewMode('student-forgot-password')}
        onLoginSuccess={(response, collegeUsn) => {
          setStudentSession({ response, collegeUsn });
          setViewMode('student-dashboard');
        }}
      />
    );
  }

  // 2.1 Role Separation: Dedicated Forgot Password Page
  if (viewMode === 'student-forgot-password') {
    return (
      <ForgotPassword
        onBackToLogin={() => setViewMode('student-login')}
        onGoToResetWithToken={(token) => {
          setResetToken(token);
          setViewMode('student-reset-password');
        }}
      />
    );
  }

  // 2.2 Role Separation: Dedicated Reset Password Page
  if (viewMode === 'student-reset-password') {
    return (
      <ResetPassword
        token={resetToken}
        onBackToLogin={() => {
          setResetToken('');
          setViewMode('student-login');
        }}
        onGoToForgotPassword={() => {
          setResetToken('');
          setViewMode('student-forgot-password');
        }}
      />
    );
  }

  // 3. Role Separation: Dedicated Student Registration Form
  if (viewMode === 'student-register') {
    return (
      <StudentRegister
        onBackToWelcome={() => setViewMode('welcome')}
        onGoToLogin={() => setViewMode('student-login')}
      />
    );
  }

  // 4. Role Separation: Dedicated Student Dashboard (Post-Login Session Route Guard)
  if (viewMode === 'student-dashboard') {
    if (!studentSession) {
      setViewMode('student-login');
      return null;
    }

    return (
      <StudentDashboard
        loginData={studentSession.response}
        collegeUsn={studentSession.collegeUsn}
        onLogout={() => {
          setStudentSession(null);
          setViewMode('welcome');
        }}
      />
    );
  }

  // 5. Role Separation: Dedicated Administrator Login
  if (viewMode === 'admin-login') {
    return (
      <AdminLogin
        onBackToWelcome={() => setViewMode('welcome')}
        onLoginSuccess={() => {
          setViewMode('admin');
          setCurrentPage('dashboard');
        }}
      />
    );
  }

  // 6. Role Separation: If admin mode is reached without authentication, show Admin Login
  if (viewMode === 'admin' && !adminAuth.isAuthenticated()) {
    return (
      <AdminLogin
        onBackToWelcome={() => setViewMode('welcome')}
        onLoginSuccess={() => {
          setViewMode('admin');
          setCurrentPage('dashboard');
        }}
      />
    );
  }

  // 7. Role Separation: Full Administrator Suite (11 Core Modules)
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        activeAlertCount={activeAlertCount}
        onExitAdmin={handleExitAdmin}
      />

      {/* Main Admin Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar: Exactly 11 Modules */}
        <Sidebar
          currentPage={currentPage}
          onSelectPage={setCurrentPage}
          deadZoneCount={deadZones.length}
          alertCount={activeAlertCount}
          onExitAdmin={handleExitAdmin}
        />

        {/* Dynamic Page Container */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950">
          {/* Module 1: Dashboard */}
          {currentPage === 'dashboard' && (
            <Dashboard
              summary={summary}
              floor={floor}
              onNavigate={setCurrentPage}
              onSelectDeadZone={(dz) => {
                setSelectedDeadZone(dz);
                setCurrentPage('dead-zone-prediction');
              }}
            />
          )}

          {/* Module 2: Student Management */}
          {currentPage === 'student-management' && <StudentManagement />}

          {/* Module 3: Gateway & Quotas */}
          {currentPage === 'gateway-quotas' && <GatewayQuotas />}

          {/* Module 4: Wi-Fi Coverage */}
          {currentPage === 'wifi-coverage' && (
            <CoverageMap
              floor={floor}
              measurements={measurements}
              deadZones={deadZones}
              predictedGrid={predictedGrid}
              recommendations={recommendations}
              onSelectDeadZone={(dz) => {
                setSelectedDeadZone(dz);
                setCurrentPage('dead-zone-prediction');
              }}
            />
          )}

          {/* Module 5: Dead-Zone Prediction */}
          {currentPage === 'dead-zone-prediction' && (
            <DeadZonePrediction
              predictedGrid={predictedGrid}
              currentDeadZones={deadZones}
              floor={floor}
              onSelectDeadZone={(dz) => {
                setSelectedDeadZone(dz);
              }}
            />
          )}

          {/* Module 6: AP Optimization */}
          {currentPage === 'ap-optimization' && (
            <APOptimization
              recommendations={recommendations}
              deadZones={deadZones}
              floor={floor}
              onRunBeforeAfter={handleRunBeforeAfter}
              isRunningBeforeAfter={isRunningBeforeAfter}
              onNavigate={setCurrentPage}
            />
          )}

          {/* Module 7: Before vs After */}
          {currentPage === 'before-after' && (
            <BeforeAfter comparison={comparison} floor={floor} />
          )}

          {/* Module 8: Network Analytics */}
          {currentPage === 'network-analytics' && (
            <NetworkAnalytics measurements={measurements} floor={floor} />
          )}

          {/* Module 9: Alerts */}
          {currentPage === 'alerts' && (
            <Alerts alerts={alerts} onResolveAlert={handleResolveAlert} />
          )}

          {/* Module 10: Simulation & Testing */}
          {currentPage === 'simulation-testing' && (
            <SimulationControl
              floorId={floorId}
              currentFloor={floor}
              buildings={buildings}
              onSimulationComplete={() => refreshAllData(floorId)}
              onNavigateToDeadZones={(dz) => {
                setSelectedDeadZone(dz);
                setCurrentPage('dead-zone-prediction');
              }}
            />
          )}

          {/* Module 11: System Diagnostics */}
          {currentPage === 'system-diagnostics' && (
            <SystemDiagnostics
              metrics={mlMetrics}
              onModelRetrained={(m) => {
                setMLMetrics(m);
                refreshAllData(floorId);
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
