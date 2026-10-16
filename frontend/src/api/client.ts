import axios from 'axios';
import {
  Building,
  Floor,
  Measurement,
  DeadZone,
  PredictionGridPoint,
  MLModelMetrics,
  APRecommendation,
  BeforeAfterComparison,
  Alert,
  DashboardSummary,
  DeadZoneAnalyticsSummary,
  LiveWifiStatus,
  SurveyMeasurement,
  SurveySession,
  SurveyAnalysisResult,
  Student,
  StudentRegistrationRequest,
  StudentRegistrationResponse,
  StudentSelfProfile,
  GatewaySession,
  GatewayLiveClient,
  GatewayStatus,
  GatewayTelemetry,
  GatewaySessionsResponse,
  GatewayEvent,
  StudentLoginRequest,
  StudentLoginResponse,
  AdminUser,
  AdminLoginRequest,
  AdminLoginResponse,
  DemoOtpResponse,
  PasswordResetRequestResponse,
  PasswordResetVerifyTokenResponse,
  PasswordResetConfirmPayload,
  PasswordResetConfirmResponse,
} from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Admin Token Management
const ADMIN_TOKEN_KEY = 'campus_wifi_admin_token';

export const adminAuth = {
  getToken: (): string | null => {
    try {
      return localStorage.getItem(ADMIN_TOKEN_KEY);
    } catch {
      return null;
    }
  },
  setToken: (token: string): void => {
    try {
      localStorage.setItem(ADMIN_TOKEN_KEY, token);
    } catch {}
  },
  clearToken: (): void => {
    try {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
    } catch {}
  },
  isAuthenticated: (): boolean => {
    return !!adminAuth.getToken();
  },
};

// Attach admin token automatically to outgoing requests if available
apiClient.interceptors.request.use((config) => {
  const token = adminAuth.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Building & Floor
  getDefaultBuilding: async (): Promise<Building> => {
    const res = await apiClient.get<Building>('/buildings/default');
    return res.data;
  },
  getFloor: async (floorId: number): Promise<Floor> => {
    const res = await apiClient.get<Floor>(`/buildings/floors/${floorId}`);
    return res.data;
  },

  // Dashboard & Demo Pipeline
  getDashboardSummary: async (floorId: number): Promise<DashboardSummary> => {
    const res = await apiClient.get<DashboardSummary>(`/dashboard/summary/${floorId}`);
    return res.data;
  },
  generateDemo: async (scenarioName: string = 'Laboratory Dead Zone'): Promise<any> => {
    const res = await apiClient.post(`/dashboard/demo?scenario_name=${encodeURIComponent(scenarioName)}`);
    return res.data;
  },

  // Simulation
  getScenarios: async (): Promise<string[]> => {
    const res = await apiClient.get<string[]>('/simulation/scenarios');
    return res.data;
  },
  applyScenario: async (floorId: number, scenarioName: string): Promise<any> => {
    const res = await apiClient.post(`/simulation/scenario/apply?floor_id=${floorId}&scenario_name=${encodeURIComponent(scenarioName)}`);
    return res.data;
  },
  runSimulation: async (params: {
    floor_id: number;
    scenario_name?: string;
    grid_spacing?: number;
    include_noise?: boolean;
    save_to_db?: boolean;
  }): Promise<any> => {
    const res = await apiClient.post('/simulation/run', params);
    return res.data;
  },
  getRunMeasurements: async (runId: number): Promise<Measurement[]> => {
    const res = await apiClient.get<Measurement[]>(`/simulation/runs/${runId}/measurements`);
    return res.data;
  },

  // Dead Zones
  detectDeadZones: async (runId: number): Promise<DeadZone[]> => {
    const res = await apiClient.post<DeadZone[]>('/dead-zones/detect', { run_id: runId });
    return res.data;
  },
  getDeadZonesForRun: async (runId: number): Promise<DeadZone[]> => {
    const res = await apiClient.get<DeadZone[]>(`/dead-zones/run/${runId}`);
    return res.data;
  },
  getDeadZoneAnalytics: async (floorId: number): Promise<DeadZoneAnalyticsSummary> => {
    const res = await apiClient.get<DeadZoneAnalyticsSummary>(`/dead-zones/analytics/summary/${floorId}`);
    return res.data;
  },

  // Machine Learning
  trainModel: async (params?: { test_size?: number; n_estimators?: number; random_state?: number }): Promise<MLModelMetrics> => {
    const res = await apiClient.post<MLModelMetrics>('/ml/train', params || {});
    return res.data;
  },
  getMLMetrics: async (): Promise<MLModelMetrics> => {
    const res = await apiClient.get<MLModelMetrics>('/ml/metrics');
    return res.data;
  },
  predictGrid: async (params: { run_id: number; floor_id: number; grid_spacing?: number }): Promise<PredictionGridPoint[]> => {
    const res = await apiClient.post<PredictionGridPoint[]>('/ml/predict-grid', params);
    return res.data;
  },
  getGridPredictions: async (runId: number): Promise<PredictionGridPoint[]> => {
    const res = await apiClient.get<PredictionGridPoint[]>(`/ml/predictions/${runId}`);
    return res.data;
  },

  // Optimization & Verification
  getRecommendations: async (floorId: number, runId: number): Promise<APRecommendation[]> => {
    const res = await apiClient.post<APRecommendation[]>('/optimizer/recommend', {
      floor_id: floorId,
      run_id: runId,
      max_recommendations: 3,
    });
    return res.data;
  },
  runBeforeAfter: async (floorId: number, baselineRunId: number): Promise<BeforeAfterComparison> => {
    const res = await apiClient.post<BeforeAfterComparison>(
      `/optimizer/before-after?floor_id=${floorId}&baseline_run_id=${baselineRunId}`
    );
    return res.data;
  },

  // Alerts
  getAlerts: async (status?: string): Promise<Alert[]> => {
    const query = status ? `?status=${status}` : '';
    const res = await apiClient.get<Alert[]>(`/alerts${query}`);
    return res.data;
  },
  resolveAlert: async (alertId: number): Promise<Alert> => {
    const res = await apiClient.put<Alert>(`/alerts/${alertId}/resolve`);
    return res.data;
  },

  // CSV Import
  uploadCSV: async (file: File, floorId: number = 1): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/import/csv?floor_id=${floorId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // Real College Survey Mode
  getLiveWifi: async (targetIp?: string): Promise<LiveWifiStatus> => {
    const query = targetIp ? `?target_ip=${encodeURIComponent(targetIp)}` : '';
    const res = await apiClient.get<LiveWifiStatus>(`/survey/current-wifi${query}`);
    return res.data;
  },
  getDefaultGateway: async (): Promise<{ default_gateway: string }> => {
    const res = await apiClient.get<{ default_gateway: string }>('/survey/gateway');
    return res.data;
  },
  createSurveySession: async (session: {
    name: string;
    building_id: number;
    floor_id: number;
    ping_target?: string;
    floorplan_width_m?: number;
    floorplan_height_m?: number;
    notes?: string;
  }): Promise<SurveySession> => {
    const res = await apiClient.post<SurveySession>('/survey/sessions', session);
    return res.data;
  },
  getSurveySessions: async (floorId?: number): Promise<SurveySession[]> => {
    const query = floorId ? `?floor_id=${floorId}` : '';
    const res = await apiClient.get<SurveySession[]>(`/survey/sessions${query}`);
    return res.data;
  },
  getSurveySession: async (sessionId: number): Promise<SurveySession> => {
    const res = await apiClient.get<SurveySession>(`/survey/sessions/${sessionId}`);
    return res.data;
  },
  captureSurveyMeasurement: async (
    sessionId: number,
    data: { x: number; y: number; notes?: string; target_ip?: string }
  ): Promise<SurveyMeasurement> => {
    const res = await apiClient.post<SurveyMeasurement>(`/survey/sessions/${sessionId}/capture`, data);
    return res.data;
  },
  clearSurveyMeasurements: async (sessionId: number): Promise<{ message: string; count: number }> => {
    const res = await apiClient.delete<{ message: string; count: number }>(`/survey/sessions/${sessionId}/measurements`);
    return res.data;
  },
  analyzeSurveySession: async (sessionId: number): Promise<SurveyAnalysisResult> => {
    const res = await apiClient.post<SurveyAnalysisResult>(`/survey/sessions/${sessionId}/analyze`);
    return res.data;
  },
  exportSurveyCsvUrl: (sessionId: number): string => {
    return `${API_BASE}/survey/sessions/${sessionId}/export-csv`;
  },
  sampleSurveyCsvUrl: (): string => {
    return `${API_BASE}/survey/sample-csv`;
  },

  // Campus Gateway & Student Quotas (OpenWrt / OpenNDS FAS)
  getGatewayStatus: async (): Promise<GatewayStatus> => {
    const res = await apiClient.get<GatewayStatus>('/gateway/status');
    return res.data;
  },
  getGatewayTelemetry: async (): Promise<GatewayTelemetry> => {
    const res = await apiClient.get<GatewayTelemetry>('/gateway/telemetry');
    return res.data;
  },
  getGatewayStudents: async (params?: {
    view?: 'ordinary' | 'demo_testing' | 'all';
    batch_year?: number;
    department_code?: string;
    approval_status?: string;
    search?: string;
  }): Promise<Student[]> => {
    const res = await apiClient.get<Student[]>('/gateway/students', { params });
    return res.data;
  },
  registerStudent: async (data: StudentRegistrationRequest): Promise<StudentRegistrationResponse> => {
    const res = await apiClient.post<StudentRegistrationResponse>('/gateway/register', data);
    return res.data;
  },
  getStudentSelfProfile: async (data: { college_usn: string; password: string }): Promise<StudentSelfProfile> => {
    const res = await apiClient.post<StudentSelfProfile>('/gateway/students/me', data);
    return res.data;
  },
  adminSetApproval: async (studentId: string, approval_status: string, admin_notes?: string): Promise<Student> => {
    const res = await apiClient.post<Student>(`/gateway/students/${encodeURIComponent(studentId)}/approval`, {
      approval_status,
      admin_notes,
    });
    return res.data;
  },
  getGatewayStudent: async (studentId: string): Promise<Student> => {
    const res = await apiClient.get<Student>(`/gateway/students/${encodeURIComponent(studentId)}`);
    return res.data;
  },
  resetStudentQuota: async (studentId: string): Promise<Student> => {
    const res = await apiClient.post<Student>(`/gateway/students/${encodeURIComponent(studentId)}/reset-quota`);
    return res.data;
  },
  loginStudent: async (payload: StudentLoginRequest): Promise<StudentLoginResponse> => {
    const res = await apiClient.post<StudentLoginResponse>('/gateway/login', payload);
    return res.data;
  },
  getGatewaySessions: async (): Promise<GatewaySessionsResponse> => {
    const res = await apiClient.get<GatewaySessionsResponse>('/gateway/sessions');
    return res.data;
  },
  deauthClient: async (mac: string): Promise<{ success: boolean; message: string; mac: string }> => {
    const res = await apiClient.post<{ success: boolean; message: string; mac: string }>(
      `/gateway/deauth/${encodeURIComponent(mac)}`
    );
    return res.data;
  },
  getPortalLanding: async (params?: Record<string, string>): Promise<any> => {
    const res = await apiClient.get('/gateway/portal', { params });
    return res.data;
  },

  // Administrator Management & Audit Log
  adminLogin: async (req: AdminLoginRequest): Promise<AdminLoginResponse> => {
    const res = await apiClient.post<AdminLoginResponse>('/gateway/admin/login', req);
    if (res.data.token) {
      adminAuth.setToken(res.data.token);
    }
    return res.data;
  },
  adminLogout: async (): Promise<any> => {
    try {
      await apiClient.post('/gateway/admin/logout');
    } finally {
      adminAuth.clearToken();
    }
  },
  adminGetMe: async (): Promise<AdminUser> => {
    const res = await apiClient.get<AdminUser>('/gateway/admin/me');
    return res.data;
  },
  adminGetEvents: async (limit: number = 50, eventType?: string): Promise<GatewayEvent[]> => {
    const query = eventType ? `?limit=${limit}&event_type=${encodeURIComponent(eventType)}` : `?limit=${limit}`;
    const res = await apiClient.get<GatewayEvent[]>(`/gateway/admin/events${query}`);
    return res.data;
  },
  adminCreateStudent: async (student: {
    college_usn?: string;
    student_id: string;
    name: string;
    department?: string;
    academic_year?: string;
    daily_quota_mb?: number;
    session_timeout_mins?: number;
    password: string;
    is_active?: boolean;
  }): Promise<Student> => {
    const res = await apiClient.post<Student>('/gateway/admin/students', student);
    return res.data;
  },
  adminUpdateStudent: async (studentId: string, updates: Partial<Student> & { password?: string }): Promise<Student> => {
    const res = await apiClient.put<Student>(`/gateway/admin/students/${encodeURIComponent(studentId)}`, updates);
    return res.data;
  },
  adminResetQuota: async (studentId: string): Promise<Student> => {
    const res = await apiClient.post<Student>(`/gateway/admin/students/${encodeURIComponent(studentId)}/reset-quota`);
    return res.data;
  },
  adminDeauthClient: async (mac: string): Promise<any> => {
    const res = await apiClient.post(`/gateway/admin/deauth/${encodeURIComponent(mac)}`);
    return res.data;
  },

  // Demo OTP Verification Simulator
  requestDemoOtp: async (collegeUsn: string): Promise<DemoOtpResponse> => {
    const res = await apiClient.post<DemoOtpResponse>('/gateway/otp/request', { college_usn: collegeUsn });
    return res.data;
  },

  // Secure Password Reset Workflows
  requestPasswordReset: async (identifier: string): Promise<PasswordResetRequestResponse> => {
    const res = await apiClient.post<PasswordResetRequestResponse>('/gateway/password-reset/request', { identifier });
    return res.data;
  },
  verifyPasswordResetToken: async (token: string): Promise<PasswordResetVerifyTokenResponse> => {
    const res = await apiClient.post<PasswordResetVerifyTokenResponse>('/gateway/password-reset/verify-token', { token });
    return res.data;
  },
  confirmPasswordReset: async (payload: PasswordResetConfirmPayload): Promise<PasswordResetConfirmResponse> => {
    const res = await apiClient.post<PasswordResetConfirmResponse>('/gateway/password-reset/confirm', payload);
    return res.data;
  },
};
