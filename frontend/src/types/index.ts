export interface Room {
  id: number;
  floor_id: number;
  name: string;
  room_type: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
}

export interface Wall {
  id: number;
  floor_id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  wall_type: string;
  attenuation_db: number;
}

export interface AccessPoint {
  id: number;
  floor_id: number;
  name: string;
  x: number;
  y: number;
  tx_power_dbm: number;
  frequency_ghz: number;
  channel: number;
  ssid: string;
  is_active: boolean;
  is_recommended: boolean;
  created_at?: string;
}

export interface Floor {
  id: number;
  building_id: number;
  floor_number: number;
  name: string;
  height_meters: number;
  rooms: Room[];
  walls: Wall[];
  access_points: AccessPoint[];
}

export interface Building {
  id: number;
  name: string;
  description?: string;
  width: number;
  height: number;
  created_at: string;
  floors: Floor[];
}

export interface Measurement {
  id: number;
  run_id: number;
  floor_id: number;
  ap_id?: number | null;
  timestamp: string;
  x: number;
  y: number;
  rssi: number;
  latency: number;
  packet_loss: number;
  throughput: number;
  distance_to_ap: number;
  wall_factor: number;
  quality_score: number;
  quality_category: 'GOOD' | 'MODERATE' | 'POOR';
}

export interface DeadZone {
  id: number;
  run_id: number;
  floor_id: number;
  name: string;
  center_x: number;
  center_y: number;
  bounding_box: { min_x: number; min_y: number; max_x: number; max_y: number };
  polygon_points: [number, number][];
  affected_area: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  num_measurements: number;
  avg_rssi: number;
  avg_latency: number;
  avg_packet_loss: number;
  avg_throughput: number;
  nearest_ap_id?: number | null;
  contributing_factors: string[];
  persistence_score: number;
  is_persistent: boolean;
  created_at: string;
}

export interface PredictionGridPoint {
  id?: number;
  run_id: number;
  floor_id: number;
  x: number;
  y: number;
  predicted_risk: 'NOT_DEAD_ZONE' | 'POTENTIAL_DEAD_ZONE';
  dead_zone_probability: number;
  confidence: number;
  nearest_ap_id?: number | null;
  estimated_rssi: number;
  estimated_latency: number;
  estimated_packet_loss: number;
  estimated_throughput: number;
  distance_to_ap: number;
  wall_factor: number;
}

export interface MLModelMetrics {
  id?: number;
  model_name: string;
  algorithm: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: number[][];
  feature_importances: Record<string, number>;
  train_sample_count: number;
  test_sample_count: number;
  trained_at: string;
  evaluation_benchmark_type?: string;
  real_survey_evaluated_count?: number;
  real_survey_accuracy?: number;
  real_survey_note?: string;
}

export interface APRecommendation {
  id: number;
  run_id: number;
  floor_id: number;
  candidate_x: number;
  candidate_y: number;
  tx_power_dbm: number;
  priority: number;
  reason: string;
  expected_dead_zone_reduction_area: number;
  expected_dead_zone_count_reduction: number;
  expected_coverage_gain_pct: number;
  created_at: string;
}

export interface BeforeAfterComparison {
  floor_id: number;
  baseline_run_id: number;
  optimized_run_id: number;
  before_dead_zone_count: number;
  after_dead_zone_count: number;
  dead_zone_count_reduction: number;
  dead_zone_count_reduction_pct: number;
  before_dead_zone_area: number;
  after_dead_zone_area: number;
  dead_zone_area_reduction: number;
  dead_zone_area_reduction_pct: number;
  before_coverage_good_pct: number;
  after_coverage_good_pct: number;
  before_coverage_poor_pct: number;
  after_coverage_poor_pct: number;
  before_avg_rssi: number;
  after_avg_rssi: number;
  rssi_improvement: number;
  before_avg_latency: number;
  after_avg_latency: number;
  latency_reduction: number;
  before_avg_packet_loss: number;
  after_avg_packet_loss: number;
  packet_loss_reduction: number;
  before_avg_throughput: number;
  after_avg_throughput: number;
  throughput_improvement: number;
  status?: string;
  area_reduction_status?: string;
  recommended_aps_added: APRecommendation[];
  before_dead_zones: DeadZone[];
  after_dead_zones: DeadZone[];
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string;
  floor_id: number;
  dead_zone_id?: number | null;
  location_x?: number | null;
  location_y?: number | null;
  status: 'ACTIVE' | 'RESOLVED';
  created_at: string;
  resolved_at?: string | null;
}

export interface DashboardSummary {
  has_data: boolean;
  floor_id: number;
  run_id?: number;
  scenario_name?: string;
  current_dead_zones: number;
  predicted_dead_zones: number;
  total_dead_zone_area: number;
  percentage_affected: number;
  high_critical_dead_zones: number;
  coverage_score: number;
  avg_rssi: number;
  avg_latency: number;
  avg_packet_loss: number;
  avg_throughput: number;
  recommended_aps_count: number;
  dead_zones: DeadZone[];
}

export interface DeadZoneAnalyticsSummary {
  has_data: boolean;
  latest_run_id?: number;
  scenario_name?: string;
  total_dead_zones: number;
  total_dead_zone_area: number;
  percentage_affected: number;
  severity_breakdown: { LOW: number; MEDIUM: number; HIGH: number; CRITICAL: number };
  critical_count: number;
  persistent_count: number;
  dead_zones: DeadZone[];
}

export interface LiveWifiStatus {
  connected: boolean;
  state?: string | null;
  ssid?: string | null;
  bssid?: string | null;
  signal_percent?: number | null;
  signal_unit: string;
  rssi_dbm?: number | null;
  is_rssi_estimated: boolean;
  channel?: number | null;
  band?: string | null;
  radio_type?: string | null;
  link_speed_mbps?: number | null;
  latency_ms?: number | null;
  packet_loss_percent?: number | null;
  ping_target?: string | null;
  ping_target_type?: string | null;
  error?: string | null;
}

export interface SurveyMeasurement {
  id: number;
  survey_id: number;
  building_id: number;
  floor_id: number;
  x: number;
  y: number;
  timestamp: string;
  ssid?: string | null;
  bssid?: string | null;
  signal_value?: number | null;
  signal_unit: string;
  rssi_estimated_dbm?: number | null;
  is_rssi_estimated: boolean;
  channel?: number | null;
  band?: string | null;
  radio_type?: string | null;
  link_speed_mbps?: number | null;
  latency_ms?: number | null;
  packet_loss_percent?: number | null;
  ping_target?: string | null;
  ping_target_type: string;
  quality_score: number;
  quality_category: 'GOOD' | 'MODERATE' | 'POOR';
  is_synthetic: boolean;
  measurement_source: string;
  notes?: string | null;
}

export interface SurveySession {
  id: number;
  name: string;
  building_id: number;
  floor_id: number;
  ping_target?: string | null;
  status: 'IN_PROGRESS' | 'COMPLETED';
  floorplan_image_path?: string | null;
  floorplan_width_m: number;
  floorplan_height_m: number;
  notes?: string | null;
  created_at: string;
  completed_at?: string | null;
  measurements: SurveyMeasurement[];
}

export interface SurveyAnalysisResult {
  survey_id: number;
  linked_simulation_run_id: number;
  total_survey_points: number;
  dead_zones: DeadZone[];
  density_warning?: string | null;
  average_rssi_dbm: number;
  average_latency_ms: number;
  average_packet_loss_pct: number;
  quality_breakdown: Record<string, number>;
}

export interface Student {
  id: number;
  college_usn?: string | null;
  student_id: string;
  name: string;
  email?: string | null;
  department: string;
  department_code?: string | null;
  batch_year?: number | null;
  academic_year: string;
  approval_status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'DISABLED';
  is_demo: boolean;
  is_designated_demo?: boolean;
  daily_quota_mb: number;
  used_quota_mb: number;
  remaining_quota_mb: number;
  quota_reset_date: string;
  session_timeout_mins: number;
  is_active: boolean;
  created_at: string;
}

export interface StudentRegistrationRequest {
  college_usn: string;
  name: string;
  password: string;
  email?: string | null;
  department?: string | null;
  academic_year?: string | null;
}

export interface StudentRegistrationResponse {
  success: boolean;
  college_usn: string;
  name: string;
  department: string;
  department_code: string;
  batch_year: number;
  academic_year: string;
  approval_status: string;
  message: string;
}

export interface StudentSelfProfile {
  college_usn: string;
  student_id: string;
  name: string;
  email?: string | null;
  department: string;
  department_code: string;
  batch_year: number;
  academic_year: string;
  approval_status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'DISABLED';
  is_active: boolean;
  daily_quota_mb: number;
  used_quota_mb: number;
  remaining_quota_mb: number;
  quota_reset_date: string;
  quota_reset_time: string;
  session_timeout_mins: number;
  is_demo: boolean;
  is_designated_demo?: boolean;
  recent_sessions: GatewaySession[];
}

export interface StudentLoginRequest {
  student_id?: string | null;
  college_usn?: string | null;
  password: string;
  client_mac: string;
  client_ip?: string | null;
  redir_url?: string | null;
  otp_code?: string | null;
  hid?: string | null;
  gatewayaddress?: string | null;
  authdir?: string | null;
  simulate_gateway?: boolean;
}

export interface StudentLoginResponse {
  success: boolean;
  message: string;
  college_usn?: string | null;
  student_id?: string | null;
  name?: string | null;
  department?: string | null;
  academic_year?: string | null;
  assigned_quota_mb?: number | null;
  used_quota_mb?: number | null;
  remaining_quota_mb?: number | null;
  session_timeout_mins?: number | null;
  client_mac?: string | null;
  gateway_authorized: boolean;
  session_id?: number | null;
  quota_reset_time?: string | null;
  upload_quota_mb?: number | null;
  download_quota_mb?: number | null;
  redir_url?: string | null;
  tok?: string | null;
  authaction_url?: string | null;
  is_simulated?: boolean;
  gateway_status_mode?: string;
}

export interface AdminUser {
  id: number;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminLoginRequest {
  username: string;
  password: string;
}

export interface AdminLoginResponse {
  success: boolean;
  token: string;
  username: string;
  full_name: string;
  role: string;
  expires_in_hours: number;
}

export interface GatewayEvent {
  id: number;
  timestamp: string;
  event_type: string;
  student_id?: string | null;
  client_mac?: string | null;
  actor: string;
  details?: string | null;
  severity: string;
}

export interface DemoOtpResponse {
  success: boolean;
  college_usn: string;
  demo_otp: string;
  message: string;
  expires_in_seconds: number;
}

export interface GatewaySession {
  id: number;
  student_id: number;
  client_mac: string;
  client_ip?: string | null;
  token?: string | null;
  session_start: string;
  session_end?: string | null;
  bytes_uploaded: number;
  bytes_downloaded: number;
  quota_assigned_kb: number;
  status: string;
  notes?: string | null;
  traffic_completeness?: 'COMPLETE' | 'LAST_KNOWN_INCOMPLETE' | 'UNCERTAIN' | 'IN_PROGRESS';
}

export interface GatewayLiveClient {
  mac: string;
  ip?: string | null;
  token?: string | null;
  state: string;
  session_start?: number | null;
  session_end?: number | null;
  upload_bytes: number;
  download_bytes: number;
  upload_quota_kb: number;
  download_quota_kb: number;
  student_id?: string | null;
  student_name?: string | null;
}

export interface GatewayStatus {
  gateway_ip: string;
  gateway_connected: boolean;
  opennds_running: boolean;
  opennds_version?: string | null;
  uptime?: string | null;
  managed_interface?: string | null;
  upstream_gateway?: string | null;
  active_clients_count: number;
  integration_mode?: string;
  mhd_port?: number;
  fas_level?: number;
  error?: string | null;
}

export interface GatewayTelemetry {
  gateway_connected: boolean;
  opennds_running: boolean;
  active_sessions_count: number;
  total_demo_students: number;
  total_allocated_quota_mb: number;
  total_consumed_quota_mb: number;
  wan_interface: string;
  wan_ip?: string | null;
  error?: string | null;
}

export interface GatewaySessionsResponse {
  gateway_connected: boolean;
  active_clients_count: number;
  live_clients: GatewayLiveClient[];
  recent_history: GatewaySession[];
  error?: string | null;
}

export interface GatewayEvent {
  id: number;
  timestamp: string;
  event_type: string;
  student_id?: string | null;
  client_mac?: string | null;
  actor: string;
  details?: string | null;
  severity: string;
}

// Password Reset Types
export interface PasswordResetRequestPayload {
  identifier: string;
}

export interface PasswordResetRequestResponse {
  success: boolean;
  message: string;
  email_configured: boolean;
}

export interface PasswordResetVerifyTokenResponse {
  valid: boolean;
  message: string;
  masked_usn?: string | null;
  masked_name?: string | null;
}

export interface PasswordResetConfirmPayload {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetConfirmResponse {
  success: boolean;
  message: string;
}
