import logging
import secrets
import hashlib
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.gateway import Student, GatewaySession, AdminUser, GatewayEvent, PasswordResetToken
from app.schemas.gateway import (
    StudentOut, StudentCreate, StudentUpdate,
    StudentRegistrationRequest, StudentRegistrationResponse,
    StudentApprovalRequest, StudentSelfProfileOut, StudentSelfProfileRequest,
    StudentLoginRequest, StudentLoginResponse,
    AdminLoginRequest, AdminLoginResponse, AdminUserOut,
    GatewayEventOut, DemoOtpRequest, DemoOtpResponse,
    GatewaySessionOut, GatewayLiveClient, GatewayStatusOut, GatewayTelemetryOut,
    PasswordResetRequest, PasswordResetRequestResponse,
    PasswordResetVerifyTokenRequest, PasswordResetVerifyTokenResponse,
    PasswordResetConfirmRequest, PasswordResetConfirmResponse
)
from app.services.usn_service import parse_and_validate_usn, determine_academic_year
from app.services.email_service import send_password_reset_email, check_rate_limit
from app.services.openwrt_service import (
    gateway_service,
    hash_password,
    verify_password,
    normalize_mac,
    is_valid_mac,
    create_admin_token,
    verify_admin_token,
    revoke_admin_token,
    generate_demo_otp,
    verify_demo_otp,
    split_quota_allocation,
    parse_fas_parameter,
    compute_fas_token,
    build_opennds_auth_url,
    get_trusted_gateway_destination,
    sanitize_authdir,
    sanitize_redirect_url,
    DEFAULT_FAS_KEY,
    BYTES_PER_MIB,
    KIB_PER_MIB,
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayCommandError,
    GatewayResponseError
)
from app.routers.portal_template import render_captive_portal_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateway", tags=["Campus Gateway & Student Quotas"])


def record_gateway_event(
    db: Session,
    event_type: str,
    student_id: Optional[str] = None,
    client_mac: Optional[str] = None,
    actor: str = "SYSTEM",
    details: Optional[str] = None,
    severity: str = "INFO"
) -> GatewayEvent:
    """Records an immutable audit event in the gateway security ledger."""
    try:
        event = GatewayEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            student_id=student_id,
            client_mac=client_mac,
            actor=actor,
            details=details,
            severity=severity
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        logger.error(f"Failed to record gateway audit event: {str(e)}")
        db.rollback()
        return None


def get_current_admin(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    Security dependency protecting all administrative endpoints.
    Accepts Bearer token in Authorization header or X-Admin-Token header.
    Rejects unauthorized access with HTTP 401.
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_admin_token:
        token = x_admin_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authorization required. Please log in as an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_info = verify_admin_token(token)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired administrator session token. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = db.query(AdminUser).filter(AdminUser.username == session_info["username"]).first()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is inactive or disabled."
        )

    return admin


def check_and_apply_daily_rollover(student: Student, current_date: Optional[date] = None) -> bool:
    """
    Applies daily quota reset when crossing a midnight date boundary.
    Dedicated exhausted demo accounts retain full consumption for viva evaluation.
    Returns True if quota was reset, False otherwise.
    """
    today = current_date or date.today()
    if student.student_id == "DEMO-EXHAUSTED" or student.college_usn == "DEMO-USN-EXH05":
        student.used_quota_mb = max(student.used_quota_mb, student.daily_quota_mb)
        student.quota_reset_date = today
        return False

    if student.quota_reset_date < today:
        student.used_quota_mb = 0.0
        student.quota_reset_date = today
        return True
    return False


def _calculate_remaining_quota(student: Student, current_date: Optional[date] = None) -> float:
    """
    Calculates remaining quota for today in Megabytes (Binary IEC: 1,024 MiB = 1 GiB),
    automatically resetting consumption if a new day has started.
    Dedicated exhausted demo accounts retain full consumption for viva evaluation.
    Never returns negative quota even if measured usage exceeds daily allowance.
    """
    check_and_apply_daily_rollover(student, current_date=current_date)
    return max(0.0, round(student.daily_quota_mb - student.used_quota_mb, 2))


# =====================================================================
# Gateway Status & Hardware Telemetry Endpoints
# =====================================================================

@router.get("/status", response_model=GatewayStatusOut)
def get_gateway_status():
    """
    Checks real-time connectivity to OpenWrt 25.12.5 and OpenNDS.
    Reports authoritative live or offline status rather than faking zero data.
    """
    try:
        nds_status = gateway_service.get_opennds_status()
        live_clients = gateway_service.get_live_clients()
        client_count = int(live_clients.get("client_list_length", 0))

        return GatewayStatusOut(
            gateway_ip=gateway_service.host,
            gateway_connected=True,
            opennds_running=nds_status.get("running", True),
            opennds_version=nds_status.get("version", "10.3.1"),
            uptime=nds_status.get("uptime", "Unknown"),
            managed_interface=nds_status.get("managed_interface", "br-lan"),
            upstream_gateway=nds_status.get("upstream_gateway", "online"),
            active_clients_count=client_count,
            integration_mode="LIVE",
            mhd_port=gateway_service.mhd_port,
            fas_level=1,
            error=None
        )
    except GatewayConnectionError as e:
        return GatewayStatusOut(
            gateway_ip=gateway_service.host,
            gateway_connected=False,
            opennds_running=False,
            integration_mode="UNAVAILABLE",
            mhd_port=gateway_service.mhd_port,
            fas_level=1,
            error=str(e)
        )
    except Exception as e:
        return GatewayStatusOut(
            gateway_ip=gateway_service.host,
            gateway_connected=False,
            opennds_running=False,
            integration_mode="UNAVAILABLE",
            mhd_port=gateway_service.mhd_port,
            fas_level=1,
            error=f"Unexpected gateway check error: {str(e)}"
        )


@router.get("/telemetry", response_model=GatewayTelemetryOut)
def get_gateway_telemetry(db: Session = Depends(get_db)):
    """
    Returns real gateway hardware telemetry, student counts, and total daily bandwidth metrics.
    Clearly distinguishes live gateway data from simulated results.
    """
    status_res = get_gateway_status()
    students = db.query(Student).all()

    total_quota = sum(s.daily_quota_mb for s in students)
    total_used = sum(s.used_quota_mb for s in students)

    wan_info = gateway_service.get_wan_traffic_telemetry()
    resolved_wan_ip = None
    if status_res.upstream_gateway and "online:" in status_res.upstream_gateway:
        try:
            part = status_res.upstream_gateway.split("online:", 1)[1]
            resolved_wan_ip = part.split(",")[0].strip()
        except Exception:
            pass

    return GatewayTelemetryOut(
        gateway_connected=status_res.gateway_connected,
        opennds_running=status_res.opennds_running,
        active_sessions_count=status_res.active_clients_count,
        total_demo_students=len(students),
        total_allocated_quota_mb=round(total_quota, 2),
        total_consumed_quota_mb=round(total_used, 2),
        wan_interface=wan_info.get("wan_interface", "eth0"),
        wan_ip=resolved_wan_ip,
        error=status_res.error
    )


# =====================================================================
# Student Public & Directory Endpoints
# =====================================================================

@router.get("/students", response_model=List[StudentOut])
def list_students(
    view: Optional[str] = Query(None, description="Filter view: 'ordinary' (real students + 1 designated demo), 'demo_testing' (demo accounts), 'all' (default)"),
    batch_year: Optional[int] = Query(None, description="Filter by admission batch year (e.g., 2023, 2024)"),
    department_code: Optional[str] = Query(None, description="Filter by department branch code (e.g., CS, CT, IT, EC, ME)"),
    approval_status: Optional[str] = Query(None, description="Filter by status (PENDING_APPROVAL, APPROVED, REJECTED, DISABLED)"),
    search: Optional[str] = Query(None, description="Search query matching USN or Student Name"),
    db: Session = Depends(get_db)
):
    """
    Lists student accounts with assigned daily quotas, usage, and approval states.
    Supports filtering by batch year, branch, approval status, search query, and view mode.
    When view='ordinary': returns genuine students plus at most ONE designated demo account.
    When view='demo_testing': returns all demo testing fixtures.
    Default (view=None or 'all'): returns all accounts, preserving backward compatibility.
    Never exposes passwords, hashes, or private keys.
    """
    query = db.query(Student)
    if batch_year:
        query = query.filter(Student.batch_year == batch_year)
    if department_code:
        query = query.filter(Student.department_code == department_code.strip().upper())
    if approval_status:
        query = query.filter(Student.approval_status == approval_status.strip().upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Student.college_usn.ilike(s)) | (Student.name.ilike(s)) | (Student.student_id.ilike(s))
        )

    students = query.order_by(Student.student_id).all()
    results = []
    for s in students:
        is_desig = bool(s.is_demo and (s.student_id == "DEMO-CSE-01" or s.college_usn == "DEMO-USN-CSE01"))

        # View mode filtering
        if view == "ordinary":
            # Genuine students plus at most ONE designated demo account
            if s.is_demo and not is_desig:
                continue
        elif view == "demo_testing":
            # Demo testing fixtures only
            if not s.is_demo:
                continue

        rem = _calculate_remaining_quota(s)
        out = StudentOut.model_validate(s)
        out.remaining_quota_mb = rem
        out.is_designated_demo = is_desig
        results.append(out)
    db.commit()
    return results


@router.post("/register", response_model=StudentRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegistrationRequest, db: Session = Depends(get_db)):
    """
    College Student Self-Registration Endpoint:
    1. Validates USN structure, batch year (e.g. 23 -> 2023), and department (e.g. CS, CT).
    2. Enforces unique registration (blocks duplicate USNs).
    3. If email provided, validates syntax and enforces unique email across approved accounts.
    4. Securely hashes password using PBKDF2-HMAC-SHA256 with random salt.
    5. Sets initial status to PENDING_APPROVAL. Internet access is NOT granted until admin approval.
    6. Records audit event in gateway security ledger.
    """
    usn_res = parse_and_validate_usn(payload.college_usn)
    if not usn_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=usn_res.error_message or "Invalid College USN format."
        )

    norm_usn = usn_res.normalized_usn

    # Check for existing duplicate account by USN or student_id
    existing = db.query(Student).filter(
        (Student.college_usn == norm_usn) | (Student.student_id == norm_usn)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student account with College USN '{norm_usn}' already exists."
        )

    # Optional email validation & uniqueness
    clean_email = None
    if payload.email and payload.email.strip():
        clean_email = payload.email.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format. Please provide a valid email address (e.g., student@college.edu.in)."
            )
        existing_email = db.query(Student).filter(func.lower(Student.email) == clean_email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A student account with email '{clean_email}' already exists."
            )

    dept_name = payload.department or usn_res.department_name or "Computer Science Core"
    acad_year = payload.academic_year or determine_academic_year(usn_res.batch_year or 2023)

    new_student = Student(
        college_usn=norm_usn,
        student_id=norm_usn,
        name=payload.name.strip(),
        email=clean_email,
        department=dept_name,
        department_code=usn_res.department_code or "CS",
        batch_year=usn_res.batch_year or 2023,
        academic_year=acad_year,
        approval_status="PENDING_APPROVAL",
        is_demo=usn_res.is_demo,
        password_hash=hash_password(payload.password),
        daily_quota_mb=1024.0,  # 1 GiB standard daily allowance
        used_quota_mb=0.0,
        quota_reset_date=date.today(),
        session_timeout_mins=120,
        is_active=False  # Inactive until administrator approves
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    record_gateway_event(
        db,
        event_type="REGISTRATION_SUBMITTED",
        student_id=norm_usn,
        actor="STUDENT",
        details=f"New student registration submitted for {norm_usn} ({payload.name.strip()}) in {dept_name} (Batch {usn_res.batch_year}). Awaiting administrator approval.",
        severity="INFO"
    )

    return StudentRegistrationResponse(
        success=True,
        college_usn=norm_usn,
        name=new_student.name,
        department=new_student.department,
        department_code=new_student.department_code or "CS",
        batch_year=new_student.batch_year or 2023,
        academic_year=new_student.academic_year,
        approval_status="PENDING_APPROVAL",
        message="Registration submitted successfully. Your account is pending administrator approval before campus Wi-Fi internet access is granted."
    )


@router.post("/students/{student_id}/approval", response_model=StudentOut)
def admin_set_student_approval(
    student_id: str,
    payload: StudentApprovalRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Administrator endpoint to approve, reject, or disable student registrations.
    Protected by server-side administrator token authentication.
    """
    clean_id = student_id.strip()
    query = (Student.student_id == clean_id) | (Student.college_usn == clean_id)
    if clean_id.isdigit():
        query = query | (Student.id == int(clean_id))
    student = db.query(Student).filter(query).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record '{clean_id}' not found."
        )

    target_status = payload.approval_status.strip().upper()
    if target_status not in ["APPROVED", "REJECTED", "DISABLED", "PENDING_APPROVAL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid approval status. Must be APPROVED, REJECTED, DISABLED, or PENDING_APPROVAL."
        )

    student.approval_status = target_status
    if target_status == "APPROVED":
        student.is_active = True
        event_name = "STUDENT_APPROVED"
        note = f"Student account approved by admin '{current_admin.username}'."
    elif target_status == "REJECTED":
        student.is_active = False
        event_name = "STUDENT_REJECTED"
        note = f"Student registration rejected by admin '{current_admin.username}'."
    elif target_status == "DISABLED":
        student.is_active = False
        event_name = "ACCOUNT_DISABLED"
        note = f"Student account disabled by admin '{current_admin.username}'."
    else:
        student.is_active = False
        event_name = "ACCOUNT_PENDING"
        note = f"Student account marked pending by admin '{current_admin.username}'."

    if payload.admin_notes:
        note += f" Note: {payload.admin_notes}"

    db.commit()
    db.refresh(student)

    record_gateway_event(
        db,
        event_type=event_name,
        student_id=student.college_usn or student.student_id,
        actor=current_admin.username,
        details=note,
        severity="INFO"
    )

    rem = _calculate_remaining_quota(student)
    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = rem
    return out


@router.post("/students/me", response_model=StudentSelfProfileOut)
def get_student_self_profile(payload: StudentSelfProfileRequest, db: Session = Depends(get_db)):
    """
    Private student self-service profile and history lookup:
    Allows authenticated students to view their own account approval status,
    daily quota balance, and session history.
    Enforces strict privacy: students can never see other students' records.
    """
    clean_usn = payload.college_usn.strip().upper()
    student = db.query(Student).filter(
        (Student.college_usn == clean_usn) | (Student.student_id == clean_usn)
    ).first()
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid College USN or password."
        )

    rem = _calculate_remaining_quota(student)
    db.commit()

    # Query this student's recent gateway sessions
    sessions = db.query(GatewaySession).filter(
        GatewaySession.student_id == student.id
    ).order_by(GatewaySession.session_start.desc()).limit(10).all()

    return StudentSelfProfileOut(
        college_usn=student.college_usn or student.student_id,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        department_code=student.department_code or "CS",
        batch_year=student.batch_year or 2023,
        academic_year=student.academic_year,
        approval_status=student.approval_status,
        is_active=student.is_active,
        daily_quota_mb=student.daily_quota_mb,
        used_quota_mb=student.used_quota_mb,
        remaining_quota_mb=rem,
        quota_reset_date=student.quota_reset_date,
        quota_reset_time="Daily at 00:00 (Midnight)",
        session_timeout_mins=student.session_timeout_mins,
        is_demo=student.is_demo,
        recent_sessions=[GatewaySessionOut.model_validate(s) for s in sessions]
    )


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Retrieves student details and remaining daily quota balance by ID or USN."""
    clean_id = student_id.strip()
    query = (Student.student_id == clean_id) | (Student.college_usn == clean_id)
    if clean_id.isdigit():
        query = query | (Student.id == int(clean_id))
    student = db.query(Student).filter(query).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record '{student_id}' not found."
        )
    rem = _calculate_remaining_quota(student)
    db.commit()
    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = rem
    return out


@router.post("/students/{student_id}/reset-quota", response_model=StudentOut)
def public_reset_student_quota(student_id: str, db: Session = Depends(get_db)):
    """
    Resets student daily data usage counter to 0 MB (useful for viva demonstration).
    Records audit event in ledger.
    """
    clean_id = student_id.strip()
    query = (Student.student_id == clean_id) | (Student.college_usn == clean_id)
    if clean_id.isdigit():
        query = query | (Student.id == int(clean_id))
    student = db.query(Student).filter(query).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record '{student_id}' not found."
        )
    student.used_quota_mb = 0.0
    student.quota_reset_date = date.today()
    db.commit()
    db.refresh(student)

    record_gateway_event(
        db,
        event_type="QUOTA_RESET",
        student_id=student.college_usn or student.student_id,
        actor="DEMO_USER",
        details=f"Daily quota consumption reset to 0.0 MiB for {student.name}. Full {student.daily_quota_mb} MiB restored.",
        severity="INFO"
    )

    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = student.daily_quota_mb
    return out


# =====================================================================
# Core Captive Portal Authentication Endpoint
# =====================================================================

@router.post("/login", response_model=StudentLoginResponse)
def student_captive_portal_login(payload: StudentLoginRequest, db: Session = Depends(get_db)):
    """
    Core Captive Portal Authentication & Gateway Quota Enforcement:
    1. Validates student credentials against USN or Student Roll Number.
    2. Enforces account active status and daily binary IEC quota limit.
    3. FAIL-CLOSED GATEWAY ENFORCEMENT: Calls ndsctl auth with strictly split
       upload and download quotas to guarantee student is NOT granted 2x quota.
    4. Records session and immutable security audit event.
    """
    # 1. Identify student by USN or student_id
    search_id = payload.college_usn or payload.student_id
    if not search_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College USN or Student ID is required for authentication."
        )

    student = db.query(Student).filter(
        (Student.college_usn == search_id.strip()) | (Student.student_id == search_id.strip())
    ).first()

    if not student:
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=search_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details=f"Authentication failed: Identifier '{search_id}' not found.",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid College USN / Student ID or password."
        )

    # Check account approval status
    if student.approval_status == "PENDING_APPROVAL":
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=student.college_usn or student.student_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details="Authentication rejected: Student account is pending administrator approval.",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account registration is pending administrator approval. Please contact the campus network administrator."
        )

    if student.approval_status == "REJECTED":
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=student.college_usn or student.student_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details="Authentication rejected: Student account registration was rejected by administrator.",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account registration was rejected by the network administrator."
        )

    if not student.is_active or student.approval_status == "DISABLED":
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=student.college_usn or student.student_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details="Authentication rejected: Student account is disabled.",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account is disabled. Contact campus network administrator."
        )

    # 2. Verify secure password hash
    if not verify_password(payload.password, student.password_hash):
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=student.college_usn or student.student_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details="Authentication failed: Incorrect password.",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid College USN / Student ID or password."
        )

    # 3. Optional Demo OTP verification
    if payload.otp_code:
        usn_key = student.college_usn or student.student_id
        if not verify_demo_otp(usn_key, payload.otp_code):
            record_gateway_event(
                db,
                event_type="LOGIN_FAILED",
                student_id=usn_key,
                client_mac=payload.client_mac,
                actor="STUDENT",
                details="Authentication failed: Invalid or expired demo OTP code.",
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired verification code."
            )

    # 4. Check remaining daily quota (Binary IEC: 1,024 MiB = 1 GiB)
    remaining_mb = _calculate_remaining_quota(student)
    if remaining_mb <= 0.0:
        record_gateway_event(
            db,
            event_type="QUOTA_EXHAUSTED",
            student_id=student.college_usn or student.student_id,
            client_mac=payload.client_mac,
            actor="STUDENT",
            details=f"Access blocked by gateway: Daily quota exhausted ({student.used_quota_mb:.1f} / {student.daily_quota_mb:.1f} MiB consumed).",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Daily data quota exhausted ({student.used_quota_mb:.1f} MiB of {student.daily_quota_mb:.1f} MiB consumed). Access blocked by OpenWrt gateway."
        )

    # 5. Validate client hardware MAC
    norm_mac = normalize_mac(payload.client_mac)
    if not is_valid_mac(norm_mac) or norm_mac in ("00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff") or norm_mac.startswith("01:00:5e"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hardware MAC address format: '{payload.client_mac}'. Expected valid unicast 6-octet address."
        )

    # Reconcile existing active sessions on this MAC for any different student
    existing_sessions = db.query(GatewaySession).filter(
        GatewaySession.client_mac == norm_mac,
        GatewaySession.status == "ACTIVE"
    ).all()
    for prev_session in existing_sessions:
        if prev_session.student_id != student.id:
            prev_session.status = "SUPERSEDED"
            prev_session.session_end = datetime.utcnow()
            prev_session.notes = (prev_session.notes or "") + f" [Reassigned to {student.college_usn or student.student_id}]"
            record_gateway_event(
                db,
                event_type="CLIENT_REASSIGNED",
                student_id=student.college_usn or student.student_id,
                client_mac=norm_mac,
                actor="SYSTEM",
                details=f"Device {norm_mac} reassigned to student {student.name}. Previous active session closed.",
                severity="INFO"
            )

    # 6. FAIL-CLOSED GATEWAY AUTHORIZATION WITH STRICT QUOTA SPLIT
    quota_kb = int(remaining_mb * KIB_PER_MIB)
    timeout_mins = student.session_timeout_mins
    is_simulated = bool(payload.simulate_gateway)

    if is_simulated:
        up_quota_kb, down_quota_kb = split_quota_allocation(quota_kb)
        gateway_authorized = True
        live_gateway_verified = False
        gateway_status_mode = "SIMULATED"
        logger.info(
            f"[SIMULATED GATEWAY] Offline evaluation session recorded for client {norm_mac} and student "
            f"{student.college_usn or student.student_id} (Up: {up_quota_kb} kB, Down: {down_quota_kb} kB)"
        )
    else:
        try:
            _, up_quota_kb, down_quota_kb = gateway_service.authorize_client(
                client_mac=norm_mac,
                session_timeout_mins=timeout_mins,
                quota_kb=quota_kb,
                student_id=student.college_usn or student.student_id,
                client_ip=payload.client_ip
            )
            gateway_authorized = True
            live_gateway_verified = True
            gateway_status_mode = "LIVE"
        except GatewayAuthenticationError as e:
            record_gateway_event(
                db,
                event_type="GATEWAY_DISCONNECTED",
                student_id=student.college_usn or student.student_id,
                client_mac=norm_mac,
                actor="SYSTEM",
                details=f"Gateway SSH authentication error: {str(e)}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenWrt gateway authentication failed: {str(e)}"
            )
        except GatewayConnectionError as e:
            record_gateway_event(
                db,
                event_type="GATEWAY_DISCONNECTED",
                student_id=student.college_usn or student.student_id,
                client_mac=norm_mac,
                actor="SYSTEM",
                details=f"Gateway connection error during authorization: {str(e)}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gateway authorization failed: OpenWrt gateway is unreachable. Internet access was NOT granted."
            )
        except GatewayCommandError as e:
            record_gateway_event(
                db,
                event_type="GATEWAY_DISCONNECTED",
                student_id=student.college_usn or student.student_id,
                client_mac=norm_mac,
                actor="SYSTEM",
                details=f"OpenNDS gateway command rejection: {str(e)}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenNDS gateway rejected client authorization: {str(e)}"
            )

    # 7. Record active session
    session = GatewaySession(
        student_id=student.id,
        client_mac=norm_mac,
        client_ip=payload.client_ip,
        session_start=datetime.utcnow(),
        quota_assigned_kb=float(quota_kb),
        status="ACTIVE",
        notes=f"{'Simulated' if is_simulated else 'Live'} FAS session for {student.name} ({student.college_usn or student.student_id})"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 8. Record audit ledger event
    record_gateway_event(
        db,
        event_type="LOGIN_SUCCESS",
        student_id=student.college_usn or student.student_id,
        client_mac=norm_mac,
        actor="STUDENT",
        details=f"{'Simulated session recorded' if is_simulated else 'Authenticated on live gateway'}. Granted {remaining_mb:.1f} MiB total (Down: {down_quota_kb/1024:.1f} MiB, Up: {up_quota_kb/1024:.1f} MiB) for {timeout_mins} mins.",
        severity="INFO"
    )

    calculated_tok = None
    authaction_url = None
    safe_redir = sanitize_redirect_url(payload.redir_url) if payload.redir_url else None
    if payload.hid:
        try:
            calculated_tok = compute_fas_token(payload.hid)
            safe_gw = get_trusted_gateway_destination(payload.gatewayaddress)
            safe_authdir = sanitize_authdir(payload.authdir)
            authaction_url = build_opennds_auth_url(
                gatewayaddress=safe_gw,
                tok=calculated_tok,
                redir_url=safe_redir,
                authdir=safe_authdir
            )
        except Exception as e:
            logger.warning(f"Could not compute FAS handshake token: {str(e)}")

    welcome_msg = (
        f"Authentication successful (Simulated Mode). Welcome {student.name}! Daily quota: {remaining_mb:.1f} MiB recorded."
        if is_simulated else
        f"Authentication successful. Welcome {student.name}! Gateway quota of {remaining_mb:.1f} MiB granted for {timeout_mins} minutes."
    )

    return StudentLoginResponse(
        success=True,
        message=welcome_msg,
        college_usn=student.college_usn,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        academic_year=student.academic_year,
        assigned_quota_mb=student.daily_quota_mb,
        used_quota_mb=student.used_quota_mb,
        remaining_quota_mb=remaining_mb,
        session_timeout_mins=timeout_mins,
        client_mac=norm_mac,
        gateway_authorized=gateway_authorized,
        live_gateway_verified=live_gateway_verified,
        is_simulated=is_simulated,
        gateway_status_mode=gateway_status_mode,
        session_id=session.id,
        quota_reset_time="Daily at 00:00 (Midnight)",
        upload_quota_mb=round(up_quota_kb / KIB_PER_MIB, 2),
        download_quota_mb=round(down_quota_kb / KIB_PER_MIB, 2),
        redir_url=safe_redir,
        tok=calculated_tok,
        authaction_url=authaction_url
    )


# =====================================================================
# OpenNDS FAS Level 1 Landing & Handshake Endpoints
# =====================================================================

@router.get("/portal")
def captive_portal_landing(
    request: Request,
    fas: Optional[str] = Query(default=None),
    authaction: Optional[str] = Query(default=None),
    tok: Optional[str] = Query(default=None),
    clientip: Optional[str] = Query(default=None),
    clientmac: Optional[str] = Query(default=None),
    gatewayaddress: Optional[str] = Query(default=None),
    gatewayport: Optional[str] = Query(default=None),
    redir: Optional[str] = Query(default=None),
    format: Optional[str] = Query(default=None)
):
    """
    OpenNDS Forward Authentication Service (FAS) Level 1 Landing Endpoint.
    1. If `fas` is supplied (Level 1), decodes base64 parameters:
       clientmac, clientip, hid, gatewayaddress, authdir, originurl.
    2. If request Accept header includes text/html or format=html, serves
       a mobile-friendly, self-contained captive portal HTML login form.
    3. If Accept header requests JSON or format=json, returns structured JSON
       for API consumers and automated test compatibility.
    """
    params: Dict[str, Any] = {}
    if fas:
        params = parse_fas_parameter(fas)
        params["fas"] = fas

    # Override / fallback with any explicitly provided query parameters
    if clientmac:
        params["clientmac"] = normalize_mac(clientmac)
    if clientip:
        params["clientip"] = clientip
    if tok:
        params["tok"] = tok

    # Strictly validate gateway destination, authdir, and redirect URL
    raw_gw = gatewayaddress or (f"{settings.OPENWRT_HOST}:{gatewayport}" if gatewayport else params.get("gatewayaddress"))
    trusted_gw = get_trusted_gateway_destination(raw_gw)
    safe_authdir = sanitize_authdir(params.get("authdir", "opennds_auth"))
    safe_redir = sanitize_redirect_url(params.get("originurl") or redir)

    params["gatewayaddress"] = trusted_gw
    params["authdir"] = safe_authdir
    params["originurl"] = safe_redir
    params["authaction"] = f"http://{trusted_gw}/{safe_authdir}/"

    accept_header = request.headers.get("accept", "").lower()
    wants_json = (format == "json") or ("application/json" in accept_header and "text/html" not in accept_header)
    wants_html = (format == "html") or ("text/html" in accept_header) or (fas is not None and format != "json")

    # If specifically JSON or standard non-browser test call
    if wants_json or (not wants_html and not fas):
        return {
            "status": "portal_ready",
            "service": "Campus OpenWrt Captive Portal",
            "client_mac": params.get("clientmac") or (normalize_mac(clientmac) if clientmac else None),
            "client_ip": params.get("clientip") or clientip,
            "token": params.get("tok") or tok,
            "hid": params.get("hid"),
            "gatewayaddress": trusted_gw,
            "authaction": f"http://{trusted_gw}/{safe_authdir}/",
            "redir_url": safe_redir,
            "fas_hash": fas,
            "instructions": "Submit student credentials via POST /api/v1/gateway/login or /portal/submit to authenticate."
        }

    # Render HTML captive portal
    return HTMLResponse(content=render_captive_portal_html(params), status_code=200)


@router.post("/portal/submit")
def captive_portal_form_submit(
    request: Request,
    college_usn: str = Form(...),
    password: str = Form(...),
    client_mac: str = Form(...),
    client_ip: Optional[str] = Form(None),
    hid: Optional[str] = Form(None),
    gatewayaddress: Optional[str] = Form(None),
    authdir: Optional[str] = Form("opennds_auth"),
    redir_url: Optional[str] = Form("https://www.google.com"),
    otp_code: Optional[str] = Form(None),
    fas_blob: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Standard HTML form POST handler for browser compatibility without JavaScript.
    1. Validates student credentials and remaining quota.
    2. Authorizes client on OpenWrt gateway fail-closed with quota split.
    3. Calculates OpenNDS Level 1 token tok = sha256(hid + faskey).
    4. Issues HTTP 303 redirect to http://<trusted_gatewayaddress>/opennds_auth/?tok=<tok>&redir=<redir>
       to complete the OpenNDS browser authentication sequence safely.
    """
    safe_gw = get_trusted_gateway_destination(gatewayaddress)
    safe_authdir = sanitize_authdir(authdir)
    safe_redir = sanitize_redirect_url(redir_url)
    try:
        req = StudentLoginRequest(
            college_usn=college_usn,
            student_id=college_usn,
            password=password,
            client_mac=client_mac,
            client_ip=client_ip,
            redir_url=safe_redir,
            otp_code=otp_code,
            hid=hid,
            gatewayaddress=safe_gw,
            authdir=safe_authdir
        )
        login_res = student_captive_portal_login(req, db=db)
        target_url = login_res.authaction_url or login_res.redir_url or safe_redir or "https://www.google.com"
        clean_target = sanitize_redirect_url(target_url, fallback="https://www.google.com")
        return RedirectResponse(url=clean_target, status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        params = {
            "clientmac": client_mac,
            "clientip": client_ip,
            "hid": hid,
            "gatewayaddress": safe_gw,
            "authdir": safe_authdir,
            "originurl": safe_redir,
            "fas_blob": fas_blob,
            "error_message": str(e.detail)
        }
        return HTMLResponse(content=render_captive_portal_html(params), status_code=e.status_code)
    except Exception as e:
        params = {
            "clientmac": client_mac,
            "clientip": client_ip,
            "hid": hid,
            "gatewayaddress": safe_gw,
            "authdir": safe_authdir,
            "originurl": safe_redir,
            "fas_blob": fas_blob,
            "error_message": f"Unexpected gateway authentication error: {str(e)}"
        }
        return HTMLResponse(content=render_captive_portal_html(params), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================================
# Demo OTP Simulator Endpoints
# =====================================================================

@router.post("/otp/request", response_model=DemoOtpResponse)
def request_demo_otp(payload: DemoOtpRequest):
    """
    Generates a 6-digit demo verification OTP for viva/classroom demonstration.
    Clearly labeled: simulated verification, zero external SMS APIs required.
    """
    clean_id = payload.college_usn.strip().upper()
    code = generate_demo_otp(clean_id)
    return DemoOtpResponse(
        success=True,
        college_usn=clean_id,
        demo_otp=code,
        message="Demo Verification Code generated. (In production, dispatched via college SMS gateway)",
        expires_in_seconds=300
    )


# =====================================================================
# Protected Administrator Endpoints
# =====================================================================

@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """Authenticates administrator and issues secure bearer session token."""
    admin = db.query(AdminUser).filter(AdminUser.username == payload.username.strip()).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        record_gateway_event(
            db,
            event_type="LOGIN_FAILED",
            student_id=payload.username,
            actor="ADMIN",
            details=f"Admin login failed for username '{payload.username}'.",
            severity="SECURITY"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials."
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is disabled."
        )

    token = create_admin_token(admin.username, admin.full_name, admin.role)
    record_gateway_event(
        db,
        event_type="LOGIN_SUCCESS",
        student_id=admin.username,
        actor="ADMIN",
        details=f"Admin '{admin.username}' ({admin.full_name}) logged in successfully.",
        severity="INFO"
    )

    return AdminLoginResponse(
        success=True,
        token=token,
        username=admin.username,
        full_name=admin.full_name,
        role=admin.role,
        expires_in_hours=12
    )


@router.post("/admin/logout")
def admin_logout(admin: AdminUser = Depends(get_current_admin)):
    """Invalidates administrator session."""
    return {"success": True, "message": f"Administrator '{admin.username}' logged out."}


@router.get("/admin/me", response_model=AdminUserOut)
def admin_profile(admin: AdminUser = Depends(get_current_admin)):
    """Returns authenticated administrator profile."""
    return AdminUserOut.model_validate(admin)


@router.get("/admin/events", response_model=List[GatewayEventOut])
def list_gateway_events(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieves chronological security and quota enforcement event log.
    Protected: Accessible only to authenticated administrators.
    """
    query = db.query(GatewayEvent)
    if event_type:
        query = query.filter(GatewayEvent.event_type == event_type)
    events = query.order_by(GatewayEvent.id.desc()).limit(limit).all()
    return [GatewayEventOut.model_validate(e) for e in events]


@router.post("/admin/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def admin_create_student(
    payload: StudentCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Creates a new student account with college USN and individual quota.
    Protected: Accessible only to authenticated administrators.
    """
    # Check duplicate student_id
    if db.query(Student).filter(Student.student_id == payload.student_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student ID '{payload.student_id}' already exists."
        )

    # Check duplicate college_usn
    if payload.college_usn and db.query(Student).filter(Student.college_usn == payload.college_usn).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"College USN '{payload.college_usn}' already exists."
        )

    hashed = hash_password(payload.password)
    student = Student(
        college_usn=payload.college_usn,
        student_id=payload.student_id,
        name=payload.name,
        department=payload.department,
        academic_year=payload.academic_year,
        password_hash=hashed,
        daily_quota_mb=payload.daily_quota_mb,
        used_quota_mb=0.0,
        quota_reset_date=date.today(),
        session_timeout_mins=payload.session_timeout_mins,
        is_active=payload.is_active
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    record_gateway_event(
        db,
        event_type="STUDENT_CREATED",
        student_id=student.college_usn or student.student_id,
        actor=admin.username,
        details=f"Admin created student {student.name} (USN: {student.college_usn}, Quota: {student.daily_quota_mb} MiB).",
        severity="INFO"
    )

    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = student.daily_quota_mb
    return out


@router.put("/admin/students/{student_id}", response_model=StudentOut)
def admin_update_student(
    student_id: str,
    payload: StudentUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Updates student quota, academic year, status, or password.
    Protected: Accessible only to authenticated administrators.
    """
    student = db.query(Student).filter(
        (Student.student_id == student_id) | (Student.college_usn == student_id)
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_id}' not found."
        )

    changes = []
    if payload.name is not None:
        student.name = payload.name
        changes.append("name")
    if payload.department is not None:
        student.department = payload.department
        changes.append("department")
    if payload.academic_year is not None:
        student.academic_year = payload.academic_year
        changes.append("academic_year")
    if payload.daily_quota_mb is not None:
        student.daily_quota_mb = payload.daily_quota_mb
        changes.append(f"quota={payload.daily_quota_mb}MiB")
    if payload.session_timeout_mins is not None:
        student.session_timeout_mins = payload.session_timeout_mins
        changes.append(f"timeout={payload.session_timeout_mins}m")
    if payload.is_active is not None:
        student.is_active = payload.is_active
        changes.append(f"is_active={payload.is_active}")
    if payload.password is not None and len(payload.password) >= 4:
        student.password_hash = hash_password(payload.password)
        changes.append("password")

    db.commit()
    db.refresh(student)

    record_gateway_event(
        db,
        event_type="STUDENT_UPDATED",
        student_id=student.college_usn or student.student_id,
        actor=admin.username,
        details=f"Admin updated student parameters: {', '.join(changes)}",
        severity="INFO"
    )

    rem = _calculate_remaining_quota(student)
    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = rem
    return out


@router.post("/admin/students/{student_id}/reset-quota", response_model=StudentOut)
def admin_reset_quota(
    student_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Resets student data consumption to 0.0 MiB.
    Protected: Accessible only to authenticated administrators.
    """
    student = db.query(Student).filter(
        (Student.student_id == student_id) | (Student.college_usn == student_id)
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_id}' not found."
        )
    student.used_quota_mb = 0.0
    student.quota_reset_date = date.today()
    db.commit()
    db.refresh(student)

    record_gateway_event(
        db,
        event_type="QUOTA_RESET",
        student_id=student.college_usn or student.student_id,
        actor=admin.username,
        details=f"Admin reset data consumption to 0.0 MiB for {student.name}. Full {student.daily_quota_mb} MiB quota restored.",
        severity="INFO"
    )

    out = StudentOut.model_validate(student)
    out.remaining_quota_mb = student.daily_quota_mb
    return out


@router.post("/admin/deauth/{mac}")
def admin_deauthenticate_client(
    mac: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Terminates client connection at OpenWrt gateway and logs administrative action.
    Protected: Accessible only to authenticated administrators.
    """
    norm_mac = normalize_mac(mac)
    try:
        gateway_service.deauthorize_client(norm_mac)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to de-authorize client on OpenWrt gateway: {str(e)}"
        )

    active_session = db.query(GatewaySession).filter(
        GatewaySession.client_mac == norm_mac,
        GatewaySession.status == "ACTIVE"
    ).first()
    if active_session:
        active_session.status = "DEAUTHED"
        active_session.session_end = datetime.utcnow()
        active_session.notes = (active_session.notes or "") + " [Deauthorized by admin before final counter poll (Incomplete traffic accounting)]"
        db.commit()

    record_gateway_event(
        db,
        event_type="DEAUTH_ADMIN",
        client_mac=norm_mac,
        actor=admin.username,
        details=f"Admin manually disconnected device {norm_mac} from OpenWrt gateway.",
        severity="WARNING"
    )

    return {
        "success": True,
        "message": f"Client device '{norm_mac}' de-authenticated from gateway.",
        "mac": norm_mac
    }


# Backwards compatibility deauth endpoint
@router.post("/deauth/{mac}")
def public_deauthenticate_client(mac: str, db: Session = Depends(get_db)):
    """Public/demo de-auth endpoint with audit event logging."""
    norm_mac = normalize_mac(mac)
    try:
        gateway_service.deauthorize_client(norm_mac)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to de-authorize client on OpenWrt gateway: {str(e)}"
        )

    active_session = db.query(GatewaySession).filter(
        GatewaySession.client_mac == norm_mac,
        GatewaySession.status == "ACTIVE"
    ).first()
    if active_session:
        active_session.status = "DEAUTHED"
        active_session.session_end = datetime.utcnow()
        active_session.notes = (active_session.notes or "") + " [Deauthorized before final counter poll (Incomplete traffic accounting)]"
        db.commit()

    record_gateway_event(
        db,
        event_type="DEAUTH_ADMIN",
        client_mac=norm_mac,
        actor="DEMO_USER",
        details=f"Device {norm_mac} de-authenticated from OpenWrt gateway.",
        severity="INFO"
    )

    return {
        "success": True,
        "message": f"Client device '{norm_mac}' has been de-authenticated from the OpenWrt gateway.",
        "mac": norm_mac
    }


def get_session_router_baseline(session: GatewaySession) -> Tuple[float, float]:
    """Retrieves the previous raw router counters for this session from notes or session bytes."""
    if session.notes:
        match = re.search(r"\[router_baseline:\s*up=([\d\.]+),\s*down=([\d\.]+)\]", session.notes)
        if match:
            return (float(match.group(1)), float(match.group(2)))

    return (float(session.bytes_uploaded or 0.0), float(session.bytes_downloaded or 0.0))


def set_session_router_baseline(session: GatewaySession, up_raw: float, down_raw: float):
    """Persists the updated router baseline in session notes."""
    new_tag = f"[router_baseline: up={up_raw:.0f}, down={down_raw:.0f}]"
    if session.notes:
        if "[router_baseline:" in session.notes:
            session.notes = re.sub(r"\[router_baseline:\s*up=[\d\.]+,\s*down=[\d\.]+\]", new_tag, session.notes)
        else:
            session.notes += f" {new_tag}"
    else:
        session.notes = new_tag


# =====================================================================
# Live Connected Sessions
# =====================================================================

@router.get("/sessions")
def get_gateway_sessions(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db)
):
    """
    Retrieves live connected sessions from authoritative OpenNDS kernel counters,
    combined with student database profiles and total byte accounting.
    Reconciles stale sessions with gateway state and masks sensitive data for non-admins.
    """
    is_admin = False
    admin_token = None
    if authorization and authorization.lower().startswith("bearer "):
        admin_token = authorization[7:].strip()
    elif x_admin_token:
        admin_token = x_admin_token.strip()
    if admin_token and verify_admin_token(admin_token):
        is_admin = True

    gateway_connected = False
    opennds_clients: Dict[str, Any] = {}
    error_msg = None

    try:
        live_data = gateway_service.get_live_clients()
        gateway_connected = True
        opennds_clients = live_data.get("clients", {})
    except Exception as e:
        error_msg = str(e)

    live_client_list: List[GatewayLiveClient] = []
    students_by_id = {s.id: s for s in db.query(Student).all()}
    active_sessions = db.query(GatewaySession).filter(GatewaySession.status == "ACTIVE").all()
    sessions_by_mac = {s.client_mac: s for s in active_sessions}

    # Reconcile stale database sessions against authoritative OpenNDS clients
    if gateway_connected:
        opennds_macs = {normalize_mac(m) for m in opennds_clients.keys()}
        now = datetime.utcnow()
        for session_item in active_sessions:
            if session_item.client_mac not in opennds_macs:
                st = students_by_id.get(session_item.student_id)
                timeout_mins = st.session_timeout_mins if st else 120
                if (now - session_item.session_start).total_seconds() >= timeout_mins * 60:
                    session_item.status = "EXPIRED"
                    session_item.session_end = now
                    session_item.notes = (session_item.notes or "") + " [Reconciled: Expired from OpenNDS (Incomplete traffic accounting)]"

    for mac, details in opennds_clients.items():
        clean_mac = normalize_mac(mac)
        matched_session = sessions_by_mac.get(clean_mac)
        student_obj = students_by_id.get(matched_session.student_id) if matched_session else None

        up_bytes = int(details.get("upload_bytes", 0))
        down_bytes = int(details.get("download_bytes", 0))

        if student_obj and matched_session:
            # 1. Check and apply daily rollover if midnight boundary has crossed
            check_and_apply_daily_rollover(student_obj)

            # 2. Retrieve previous raw router baseline
            base_up, base_down = get_session_router_baseline(matched_session)
            curr_up = float(up_bytes)
            curr_down = float(down_bytes)

            delta_up = 0.0
            delta_down = 0.0
            notes_append = ""

            # Upload direction evaluation
            if curr_up < base_up:
                # Counter reset / decrease detected
                delta_up = max(0.0, curr_up)
                notes_append += f" [Accounting Uncertainty: Counter reset/decrease detected (upload: {base_up:.0f} -> {curr_up:.0f})]"
                logger.warning(f"Counter reset/decrease on session {matched_session.id} (upload: {base_up} -> {curr_up})")
                new_base_up = curr_up
            else:
                delta_up = curr_up - base_up
                new_base_up = curr_up

            # Download direction evaluation
            if curr_down < base_down:
                # Counter reset / decrease detected
                delta_down = max(0.0, curr_down)
                notes_append += f" [Accounting Uncertainty: Counter reset/decrease detected (download: {base_down:.0f} -> {curr_down:.0f})]"
                logger.warning(f"Counter reset/decrease on session {matched_session.id} (download: {base_down} -> {curr_down})")
                new_base_down = curr_down
            else:
                delta_down = curr_down - base_down
                new_base_down = curr_down

            if notes_append:
                matched_session.notes = (matched_session.notes or "") + notes_append

            delta_mb = (delta_up + delta_down) / BYTES_PER_MIB

            # 3. Accumulate actual measured usage (unclamped so actual measured traffic is preserved)
            if delta_mb > 0.0:
                student_obj.used_quota_mb = round(student_obj.used_quota_mb + delta_mb, 2)

            # 4. Monotonically accumulate session-level byte counters
            matched_session.bytes_uploaded = float(matched_session.bytes_uploaded or 0.0) + delta_up
            matched_session.bytes_downloaded = float(matched_session.bytes_downloaded or 0.0) + delta_down

            # 5. Persist the new raw router baseline for next poll
            set_session_router_baseline(matched_session, new_base_up, new_base_down)


        raw_student_id = student_obj.college_usn or student_obj.student_id if student_obj else "Unknown"
        raw_student_name = student_obj.name if student_obj else "Guest/Unregistered"
        display_token = details.get("token") if is_admin else None

        live_client_list.append(GatewayLiveClient(
            mac=clean_mac,
            ip=details.get("ip"),
            token=display_token,
            state=details.get("state", "authenticated"),
            session_start=int(details.get("session_start", 0)),
            session_end=int(details.get("session_end", 0)),
            upload_bytes=up_bytes,
            download_bytes=down_bytes,
            upload_quota_kb=int(details.get("upload_quota", 0)),
            download_quota_kb=int(details.get("download_quota", 0)),
            student_id=raw_student_id,
            student_name=raw_student_name
        ))

    db.commit()

    recent_db_sessions = db.query(GatewaySession).order_by(GatewaySession.id.desc()).limit(20).all()

    return {
        "gateway_connected": gateway_connected,
        "active_clients_count": len(live_client_list),
        "live_clients": live_client_list,
        "recent_history": [GatewaySessionOut.model_validate(s) for s in recent_db_sessions],
        "error": error_msg
    }


# =====================================================================
# Secure Student Password Reset Endpoints
# =====================================================================

@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiates secure password reset workflow:
    1. Enforces sliding window rate limiting per IP (max 5 per 15 min) and per identifier (max 3 per 15 min).
    2. Identifies student by College USN, Student Roll Number, or registered email.
    3. Strict Privacy: Returns the identical generic response for known and unknown accounts.
    4. Unapproved accounts: Pending, rejected, or disabled accounts never receive reset tokens.
    5. Token Invalidation Policy: Supersedes and invalidates any prior active tokens for this student.
    6. Stores only the SHA-256 hash of a cryptographically secure token with 15-minute expiration.
    7. Dispatches email via SMTP if configured; otherwise reports unconfigured status clearly without claiming delivery.
    8. Never exposes raw tokens or secrets in API responses, logs, or error messages.
    """
    client_ip = request.client.host if request.client else "unknown"
    clean_identifier = payload.identifier.strip()
    norm_id = clean_identifier.lower()

    # Abuse protection: Rate limiting
    if not check_rate_limit(f"ip:{client_ip}", max_requests=5, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests from this network address. Please wait 15 minutes before trying again."
        )
    if not check_rate_limit(f"id:{norm_id}", max_requests=3, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests for this account identifier. Please wait 15 minutes before trying again."
        )

    # Periodic cleanup of expired tokens older than 24 hours to bound table size
    try:
        cutoff = datetime.utcnow() - timedelta(days=1)
        db.query(PasswordResetToken).filter(PasswordResetToken.expires_at < cutoff).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()

    # Look up student by USN, student_id, or registered email
    student = db.query(Student).filter(
        (func.lower(Student.college_usn) == norm_id) |
        (func.lower(Student.student_id) == norm_id) |
        (func.lower(Student.email) == norm_id)
    ).first()

    generic_msg = (
        "If an account associated with this identifier is registered and approved, "
        "a password reset link has been dispatched to the registered email address."
    )
    unconfigured_msg = (
        "Password reset email delivery is currently disabled or unconfigured on this campus server. "
        "Please contact the campus network administrator for assistance."
    )

    # Check email configuration
    is_email_active = bool(settings.SMTP_ENABLED or (settings.ENVIRONMENT in ("development", "testing") and settings.ALLOW_DEV_RESET_MAILBOX))

    if not is_email_active:
        return PasswordResetRequestResponse(
            success=False,
            message=unconfigured_msg,
            email_configured=False
        )

    # If student does not exist, perform dummy work to mitigate timing attacks
    if not student:
        hash_password("DummyTimingProtectionPassword123!")
        return PasswordResetRequestResponse(
            success=True,
            message=generic_msg,
            email_configured=True
        )

    # Block unapproved accounts from receiving reset tokens (return generic response to prevent status enumeration)
    if student.approval_status != "APPROVED" or not student.is_active:
        record_gateway_event(
            db,
            event_type="PASSWORD_RESET_REJECTED",
            student_id=student.college_usn or student.student_id,
            actor="SYSTEM",
            details=f"Password reset blocked: Account approval status is {student.approval_status} (is_active={student.is_active}).",
            severity="WARNING"
        )
        return PasswordResetRequestResponse(
            success=True,
            message=generic_msg,
            email_configured=True
        )

    # Invalidate any prior active reset tokens for this student (Single Active Token Policy)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.student_id == student.id,
        PasswordResetToken.used_at == None,
        PasswordResetToken.is_invalidated == False
    ).update({"is_invalidated": True})

    # Generate cryptographically secure token and store only SHA-256 hash
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    user_agent = request.headers.get("user-agent", "Unknown")[:250]

    token_record = PasswordResetToken(
        student_id=student.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_invalidated=False,
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(token_record)
    db.commit()

    record_gateway_event(
        db,
        event_type="PASSWORD_RESET_REQUESTED",
        student_id=student.college_usn or student.student_id,
        actor="STUDENT",
        details=f"Password reset requested from IP {client_ip}. Single-use token generated (expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} mins).",
        severity="INFO"
    )

    # Determine recipient email
    target_email = student.email or f"{student.student_id.lower()}@campus.edu.in"

    # Dispatch email
    sent, email_status = send_password_reset_email(
        to_email=target_email,
        recipient_name=student.name,
        college_usn=student.college_usn or student.student_id,
        raw_token=raw_token
    )

    return PasswordResetRequestResponse(
        success=True,
        message=generic_msg,
        email_configured=True
    )


@router.post("/password-reset/verify-token", response_model=PasswordResetVerifyTokenResponse)
def verify_password_reset_token(payload: PasswordResetVerifyTokenRequest, db: Session = Depends(get_db)):
    """
    Validates password reset token before presenting password update form.
    Checks single-use status, expiration, tampering, and account eligibility.
    Masks student identity for privacy.
    """
    token = payload.token.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is required."
        )

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token. Please request a new link."
        )

    if record.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used and cannot be reused. Please request a new link."
        )

    if record.is_invalidated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has been invalidated by a newer reset request. Please use the latest link."
        )

    if record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has expired. Please request a new link."
        )

    student = db.query(Student).filter(Student.id == record.student_id).first()
    if not student or student.approval_status != "APPROVED" or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not eligible for password reset. Please contact administration."
        )

    # Mask name and USN for safe UI presentation
    usn = student.college_usn or student.student_id
    masked_usn = usn[:3] + "*" * max(1, len(usn) - 5) + usn[-2:] if len(usn) > 5 else "***"
    name_parts = student.name.split()
    masked_name = " ".join([p[0] + "*" * max(1, len(p) - 1) for p in name_parts])

    return PasswordResetVerifyTokenResponse(
        valid=True,
        message="Token is valid and ready for password update.",
        masked_usn=masked_usn,
        masked_name=masked_name
    )


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    """
    Applies confirmed password reset:
    1. Validates password confirmation and strength (min 6 characters).
    2. Validates token hash, single-use, expiry, and invalidation status.
    3. Hashes new password securely using PBKDF2-HMAC-SHA256 with 100,000 rounds and random salt.
    4. Marks token as used (single-use enforcement) and invalidates all tokens for this student.
    5. Revokes any existing active gateway sessions for this student.
    6. Old password immediately ceases to authenticate.
    """
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match. Please verify your new password."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    token = payload.token.strip()
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token."
        )

    if record.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used and cannot be reused."
        )

    if record.is_invalidated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has been invalidated by a newer reset request."
        )

    if record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has expired. Please request a new reset link."
        )

    student = db.query(Student).filter(Student.id == record.student_id).first()
    if not student or student.approval_status != "APPROVED" or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account is not eligible for password reset."
        )

    # Atomic conditional consumption: strictly prevents concurrent double-consumption
    now_utc = datetime.utcnow()
    rows_updated = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == record.id,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.is_invalidated == False,
        PasswordResetToken.expires_at > now_utc
    ).update({
        "used_at": now_utc,
        "is_invalidated": True
    }, synchronize_session=False)

    if rows_updated == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been consumed or invalidated."
        )

    # Securely hash new password using PBKDF2-HMAC-SHA256 with random salt
    student.password_hash = hash_password(payload.new_password)

    # Invalidate all other active reset tokens for this student
    db.query(PasswordResetToken).filter(
        PasswordResetToken.student_id == student.id,
        PasswordResetToken.id != record.id
    ).update({"is_invalidated": True})

    # Revoke any active gateway sessions for this student
    db.query(GatewaySession).filter(
        GatewaySession.student_id == student.id,
        GatewaySession.status == "ACTIVE"
    ).update({
        "status": "DEAUTHED",
        "session_end": now_utc,
        "notes": "Password reset revocation"
    })

    db.commit()

    record_gateway_event(
        db,
        event_type="PASSWORD_RESET_SUCCESS",
        student_id=student.college_usn or student.student_id,
        actor="STUDENT",
        details=f"Password successfully reset for student {student.college_usn or student.student_id}. Old password no longer authenticates.",
        severity="INFO"
    )

    return PasswordResetConfirmResponse(
        success=True,
        message="Your password has been successfully reset. You may now log in with your new password."
    )
