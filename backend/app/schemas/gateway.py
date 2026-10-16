from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    college_usn: Optional[str] = Field(default=None, description="University Serial Number (e.g., ENG23CS0518)")
    student_id: str = Field(..., description="Unique student ID or Roll Number, e.g., DEMO-CSE-01")
    name: str = Field(..., description="Student full name")
    email: Optional[str] = Field(default=None, description="Student college email address")
    department: str = Field(default="Computer Science Core")
    department_code: Optional[str] = Field(default="CS", description="Academic branch code, e.g., CS, CT, IT, EC, ME")
    batch_year: Optional[int] = Field(default=2023, description="4-digit admission batch year, e.g., 2023, 2024")
    academic_year: str = Field(default="3rd Year", description="Academic Year, e.g., 1st Year, 2nd Year, 3rd Year, 4th Year")
    approval_status: str = Field(default="PENDING_APPROVAL", description="PENDING_APPROVAL, APPROVED, REJECTED, DISABLED")
    is_demo: bool = Field(default=False, description="Flag indicating clearly labeled demo accounts")
    is_designated_demo: bool = Field(default=False, description="Flag indicating the single primary demo account visible in normal roster")
    daily_quota_mb: float = Field(default=1024.0, description="Daily gateway data quota in Megabytes (Binary IEC: 1,024 MiB = 1 GiB)")
    session_timeout_mins: int = Field(default=120, description="Maximum session duration in minutes")
    is_active: bool = Field(default=True)


class StudentCreate(StudentBase):
    password: str = Field(..., min_length=4, description="Student plaintext password to be securely hashed")


class StudentRegistrationRequest(BaseModel):
    college_usn: str = Field(..., description="College USN e.g. ENG23CS0518, ENG23CT0112")
    name: str = Field(..., min_length=2, description="Student full name")
    password: str = Field(..., min_length=6, description="Password for captive portal authentication")
    email: Optional[str] = Field(default=None, description="Optional registered email address for notifications and password reset")
    department: Optional[str] = None
    academic_year: Optional[str] = None


class StudentRegistrationResponse(BaseModel):
    success: bool
    college_usn: str
    name: str
    department: str
    department_code: str
    batch_year: int
    academic_year: str
    approval_status: str
    message: str


class StudentApprovalRequest(BaseModel):
    approval_status: str = Field(..., description="'APPROVED' or 'REJECTED'")
    admin_notes: Optional[str] = None


class StudentUpdate(BaseModel):
    college_usn: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    department_code: Optional[str] = None
    batch_year: Optional[int] = None
    academic_year: Optional[str] = None
    approval_status: Optional[str] = None
    daily_quota_mb: Optional[float] = None
    session_timeout_mins: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    college_usn: Optional[str] = None
    student_id: str
    name: str
    email: Optional[str] = None
    department: str
    department_code: Optional[str] = "CS"
    batch_year: Optional[int] = 2023
    academic_year: str = "3rd Year"
    approval_status: str = "APPROVED"
    is_demo: bool = False
    is_designated_demo: bool = False
    daily_quota_mb: float
    used_quota_mb: float
    remaining_quota_mb: float = 0.0
    quota_reset_date: date
    session_timeout_mins: int
    is_active: bool
    created_at: datetime


class StudentSelfProfileOut(BaseModel):
    college_usn: str
    student_id: str
    name: str
    email: Optional[str] = None
    department: str
    department_code: str
    batch_year: int
    academic_year: str
    approval_status: str
    is_active: bool
    daily_quota_mb: float
    used_quota_mb: float
    remaining_quota_mb: float
    quota_reset_date: date
    quota_reset_time: str = "Daily at 00:00 (Midnight)"
    session_timeout_mins: int
    is_demo: bool
    is_designated_demo: bool = False
    recent_sessions: List["GatewaySessionOut"] = []


class StudentSelfProfileRequest(BaseModel):
    college_usn: str = Field(..., description="College USN or student ID")
    password: str = Field(..., description="Student password for private profile lookup")


class StudentLoginRequest(BaseModel):
    student_id: Optional[str] = Field(default=None, description="Roll number or student ID")
    college_usn: Optional[str] = Field(default=None, description="University Serial Number")
    password: str = Field(..., description="Student password")
    client_mac: str = Field(..., description="Hardware MAC address of client device")
    client_ip: Optional[str] = Field(default=None, description="IP address assigned to client")
    redir_url: Optional[str] = Field(default=None, description="Original requested URL")
    otp_code: Optional[str] = Field(default=None, description="Optional demo verification code")
    hid: Optional[str] = Field(default=None, description="OpenNDS FAS hashed client token")
    gatewayaddress: Optional[str] = Field(default=None, description="OpenNDS gateway IP:Port, e.g., 192.168.214.2:2050")
    authdir: Optional[str] = Field(default="opennds_auth", description="OpenNDS auth endpoint directory")
    simulate_gateway: bool = Field(default=False, description="Simulate gateway authorization for offline viva demos without physical client hardware")


class StudentLoginResponse(BaseModel):
    success: bool
    message: str
    college_usn: Optional[str] = None
    student_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    assigned_quota_mb: Optional[float] = None
    used_quota_mb: Optional[float] = None
    remaining_quota_mb: Optional[float] = None
    session_timeout_mins: Optional[int] = None
    client_mac: Optional[str] = None
    gateway_authorized: bool = False
    live_gateway_verified: bool = Field(default=False, description="True only when verified against the live OpenWrt/OpenNDS router")
    is_simulated: bool = Field(default=False, description="Indicates whether authentication was executed in offline simulation mode")
    gateway_status_mode: str = Field(default="LIVE", description="Authoritative gateway status: 'LIVE', 'SIMULATED', or 'UNAVAILABLE'")
    session_id: Optional[int] = None
    quota_reset_time: Optional[str] = "Daily at 00:00 (Midnight)"
    upload_quota_mb: Optional[float] = None
    download_quota_mb: Optional[float] = None
    redir_url: Optional[str] = None
    tok: Optional[str] = Field(default=None, description="OpenNDS FAS Level 1 calculated token: sha256(hid + faskey)")
    authaction_url: Optional[str] = Field(default=None, description="Direct OpenNDS gateway URL to complete browser handshake")


class AdminLoginRequest(BaseModel):
    username: str = Field(..., description="Administrator username")
    password: str = Field(..., description="Administrator password")


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    username: str
    full_name: str
    role: str
    expires_in_hours: int = 12


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class GatewayEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: str
    student_id: Optional[str] = None
    client_mac: Optional[str] = None
    actor: str = "SYSTEM"
    details: Optional[str] = None
    severity: str = "INFO"


class DemoOtpRequest(BaseModel):
    college_usn: str = Field(..., description="Student USN or identifier to receive demo OTP")


class DemoOtpResponse(BaseModel):
    success: bool
    college_usn: str
    demo_otp: str
    message: str
    expires_in_seconds: int = 300


class GatewaySessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    client_mac: str
    client_ip: Optional[str] = None
    token: Optional[str] = None
    session_start: datetime
    session_end: Optional[datetime] = None
    bytes_uploaded: float
    bytes_downloaded: float
    quota_assigned_kb: float
    status: str
    notes: Optional[str] = None
    traffic_completeness: Optional[str] = "LAST_KNOWN_INCOMPLETE"


class GatewayLiveClient(BaseModel):
    mac: str
    ip: Optional[str] = None
    token: Optional[str] = None
    state: str = "authenticated"
    session_start: Optional[int] = None
    session_end: Optional[int] = None
    upload_bytes: int = 0
    download_bytes: int = 0
    upload_quota_kb: int = 0
    download_quota_kb: int = 0
    student_id: Optional[str] = None
    student_name: Optional[str] = None


class GatewayStatusOut(BaseModel):
    gateway_ip: str = "192.168.214.2"
    gateway_connected: bool
    opennds_running: bool
    opennds_version: Optional[str] = None
    uptime: Optional[str] = None
    managed_interface: Optional[str] = None
    upstream_gateway: Optional[str] = None
    active_clients_count: int = 0
    integration_mode: str = "LIVE"
    mhd_port: int = 2050
    fas_level: int = 1
    error: Optional[str] = None


class GatewayTelemetryOut(BaseModel):
    gateway_connected: bool
    opennds_running: bool
    active_sessions_count: int
    total_demo_students: int
    total_allocated_quota_mb: float
    total_consumed_quota_mb: float
    wan_interface: str = "eth0"
    wan_ip: Optional[str] = None
    error: Optional[str] = None


# =====================================================================
# Secure Student Password Reset Schemas
# =====================================================================

class PasswordResetRequest(BaseModel):
    identifier: str = Field(..., min_length=3, description="College USN, Student ID, or registered email address")


class PasswordResetRequestResponse(BaseModel):
    success: bool
    message: str
    email_configured: bool


class PasswordResetVerifyTokenRequest(BaseModel):
    token: str = Field(..., min_length=16, description="Cryptographically secure password reset token from email link")


class PasswordResetVerifyTokenResponse(BaseModel):
    valid: bool
    message: str
    masked_usn: Optional[str] = None
    masked_name: Optional[str] = None


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=16, description="Cryptographically secure password reset token")
    new_password: str = Field(..., min_length=6, description="New password meeting security requirements (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Confirmation of new password")


class PasswordResetConfirmResponse(BaseModel):
    success: bool
    message: str
