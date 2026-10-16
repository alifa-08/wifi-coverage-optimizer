from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Student(Base):
    """
    Individual college student account model.
    Every student maintains an isolated daily bandwidth quota, session window,
    and authentication credentials for OpenWrt gateway access.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    college_usn = Column(String(50), unique=True, index=True, nullable=True)  # Primary University Serial Number (e.g., ENG23CS0518)
    student_id = Column(String(50), unique=True, index=True, nullable=False)   # Student Roll No / Internal ID
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False, default="Computer Science Core")
    department_code = Column(String(10), nullable=True, default="CS")          # e.g., CS, CT, IT, EC, ME
    batch_year = Column(Integer, nullable=True, default=2023)                  # e.g., 2023, 2024
    academic_year = Column(String(20), nullable=False, default="3rd Year")     # e.g., 1st Year, 2nd Year, 3rd Year, 4th Year
    approval_status = Column(String(30), nullable=False, default="PENDING_APPROVAL") # PENDING_APPROVAL, APPROVED, REJECTED, DISABLED
    is_demo = Column(Boolean, nullable=False, default=False)                   # Clearly distinguishes demo accounts from real students
    email = Column(String(120), nullable=True, index=True)                     # Student college email for password reset
    password_hash = Column(String(255), nullable=False)
    daily_quota_mb = Column(Float, nullable=False, default=1024.0)             # Binary IEC: 1,024 MiB (1 GiB)
    used_quota_mb = Column(Float, nullable=False, default=0.0)
    quota_reset_date = Column(Date, nullable=False, default=date.today)
    session_timeout_mins = Column(Integer, nullable=False, default=120)        # Default 2-hour max session
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("GatewaySession", back_populates="student", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="student", cascade="all, delete-orphan")

    @property
    def is_designated_demo(self) -> bool:
        """
        True only for the single primary demonstration account visible in the ordinary student roster.
        All remaining demo fixtures belong strictly to the Demo & Testing section.
        """
        return bool(self.is_demo and (self.student_id == "DEMO-CSE-01" or self.college_usn == "DEMO-USN-CSE01"))


class AdminUser(Base):
    """
    Campus Network Administrator model for role-based authentication.
    Controls student provisioning, quota adjustments, and client terminations.
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), default="SUPERADMIN", nullable=False)  # SUPERADMIN, NETWORK_ADMIN
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class GatewayEvent(Base):
    """
    Immutable audit ledger for security, quota enforcement, and authentication events.
    Tracks login attempts, quota exhaustion cutoffs, manual de-authentications, and admin overrides.
    """
    __tablename__ = "gateway_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # LOGIN_SUCCESS, LOGIN_FAILED, QUOTA_EXHAUSTED, DEAUTH_ADMIN, etc.
    student_id = Column(String(50), nullable=True, index=True)   # USN or Roll Number
    client_mac = Column(String(20), nullable=True)
    actor = Column(String(50), default="SYSTEM", nullable=False) # SYSTEM, STUDENT, ADMIN
    details = Column(Text, nullable=True)
    severity = Column(String(20), default="INFO", nullable=False) # INFO, WARNING, ERROR, SECURITY


class GatewaySession(Base):
    """
    Authoritative connection session mapping an authenticated student
    to their physical client MAC address on OpenWrt kernel netfilter.
    """
    __tablename__ = "gateway_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    client_mac = Column(String(20), nullable=False, index=True)
    client_ip = Column(String(50), nullable=True)
    token = Column(String(64), nullable=True)
    session_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_end = Column(DateTime, nullable=True)
    bytes_uploaded = Column(Float, default=0.0)    # Raw bytes uploaded
    bytes_downloaded = Column(Float, default=0.0)  # Raw bytes downloaded
    quota_assigned_kb = Column(Float, nullable=False)  # Kilobytes programmed into OpenNDS kernel
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRED, QUOTA_EXCEEDED, DEAUTHED
    notes = Column(Text, nullable=True)

    student = relationship("Student", back_populates="sessions")

    @property
    def traffic_completeness(self) -> str:
        """
        Explicit, backward-compatible evaluation of accounting completeness:
        1. 'UNCERTAIN': If counter resets, anomalies, or accounting uncertainties occurred.
        2. 'COMPLETE': ONLY if affirmative evidence of verified final counter collection is present
           ([FINAL_COUNTER_VERIFIED]).
        3. 'IN_PROGRESS': If the session is currently ACTIVE without anomalies.
        4. 'LAST_KNOWN_INCOMPLETE': All terminal sessions (EXPIRED, DEAUTHED, SUPERSEDED, etc.)
           that ended without verified final counter collection, including legacy records.
        """
        notes_str = (self.notes or "").lower()
        if any(marker in notes_str for marker in [
            "uncertainty",
            "anomaly",
            "counter reset",
            "counter decrease"
        ]):
            return "UNCERTAIN"

        if "[final_counter_verified]" in notes_str:
            return "COMPLETE"

        if self.status == "ACTIVE":
            return "IN_PROGRESS"

        return "LAST_KNOWN_INCOMPLETE"


class PasswordResetToken(Base):
    """
    Cryptographically secure, single-use password reset token store.
    Stores only the SHA-256 hash of raw tokens. Expired and used tokens
    are rendered strictly invalid.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    is_invalidated = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    student = relationship("Student", back_populates="reset_tokens")


def seed_default_students(db):
    """
    Seed initial clearly labeled demo students with USNs and academic years
    for college Wi-Fi captive portal demonstration.
    """
    from app.services.openwrt_service import hash_password
    demo_records = [
        {
            "college_usn": "DEMO-USN-CSE01",
            "student_id": "DEMO-CSE-01",
            "name": "Demo Student (CSE)",
            "department": "Computer Science Core",
            "department_code": "CS",
            "batch_year": 2023,
            "academic_year": "3rd Year",
            "approval_status": "APPROVED",
            "is_demo": True,
            "email": "demo.cse01@campus.edu.in",
            "password_hash": hash_password("Campus@2026"),
            "daily_quota_mb": 1024.0,  # 1 GiB standard
            "used_quota_mb": 0.0,
            "quota_reset_date": date.today(),
            "session_timeout_mins": 120,
            "is_active": True,
        },
        {
            "college_usn": "DEMO-USN-IT02",
            "student_id": "DEMO-IT-02",
            "name": "Demo Student (IT)",
            "department": "Information Technology",
            "department_code": "IT",
            "batch_year": 2023,
            "academic_year": "3rd Year",
            "approval_status": "APPROVED",
            "is_demo": True,
            "email": "demo.it02@campus.edu.in",
            "password_hash": hash_password("Campus@2026"),
            "daily_quota_mb": 2048.0,  # 2 GiB
            "used_quota_mb": 0.0,
            "quota_reset_date": date.today(),
            "session_timeout_mins": 180,
            "is_active": True,
        },
        {
            "college_usn": "DEMO-USN-ECE03",
            "student_id": "DEMO-ECE-03",
            "name": "Demo Student (ECE)",
            "department": "Electronics & Communication",
            "department_code": "EC",
            "batch_year": 2024,
            "academic_year": "2nd Year",
            "approval_status": "APPROVED",
            "is_demo": True,
            "email": "demo.ece03@campus.edu.in",
            "password_hash": hash_password("Campus@2026"),
            "daily_quota_mb": 512.0,   # 512 MiB
            "used_quota_mb": 0.0,
            "quota_reset_date": date.today(),
            "session_timeout_mins": 90,
            "is_active": True,
        },
        {
            "college_usn": "DEMO-USN-ME04",
            "student_id": "DEMO-MECH-04",
            "name": "Demo Student (Mech)",
            "department": "Mechanical Engineering",
            "department_code": "ME",
            "batch_year": 2022,
            "academic_year": "4th Year",
            "approval_status": "APPROVED",
            "is_demo": True,
            "email": "demo.mech04@campus.edu.in",
            "password_hash": hash_password("Campus@2026"),
            "daily_quota_mb": 256.0,   # 256 MiB
            "used_quota_mb": 0.0,
            "quota_reset_date": date.today(),
            "session_timeout_mins": 60,
            "is_active": True,
        },
        {
            "college_usn": "DEMO-USN-EXH05",
            "student_id": "DEMO-EXHAUSTED",
            "name": "Demo Student (Quota Exhausted)",
            "department": "Computer Science Core",
            "department_code": "CS",
            "batch_year": 2025,
            "academic_year": "1st Year",
            "approval_status": "APPROVED",
            "is_demo": True,
            "email": "demo.exhausted@campus.edu.in",
            "password_hash": hash_password("Campus@2026"),
            "daily_quota_mb": 500.0,
            "used_quota_mb": 500.0,   # 100% consumed for testing quota block
            "quota_reset_date": date.today(),
            "session_timeout_mins": 120,
            "is_active": True,
        },
    ]

    for item in demo_records:
        existing = db.query(Student).filter(
            (Student.student_id == item["student_id"]) | (Student.college_usn == item["college_usn"])
        ).first()
        if not existing:
            db.add(Student(**item))
        else:
            # Backfill college_usn, academic_year, batch_year, department_code, approval_status, is_demo, email if missing
            if not existing.college_usn:
                existing.college_usn = item["college_usn"]
            if not existing.academic_year:
                existing.academic_year = item["academic_year"]
            if existing.batch_year is None:
                existing.batch_year = item["batch_year"]
            if not existing.department_code:
                existing.department_code = item["department_code"]
            if not existing.approval_status:
                existing.approval_status = item["approval_status"]
            if not existing.email:
                existing.email = item["email"]
            existing.is_demo = True

    # Seed default administrator account if none exists
    admin_exists = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if not admin_exists:
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("Admin@Campus2026"),
            full_name="Campus Network Administrator",
            role="SUPERADMIN",
            is_active=True,
        )
        db.add(admin)

    db.commit()
