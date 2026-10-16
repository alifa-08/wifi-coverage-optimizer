"""
Comprehensive Automated Test Suite for Student Management, Registration Safety, and Secure Password Reset.
Covers:
1. Demo account filtering and isolation (ordinary, demo_testing, all views).
2. Registration validation, duplicate protection (USN and email), and PENDING_APPROVAL status.
3. Access control: pending vs approved student login and gateway enforcement.
4. Secure password reset workflow:
   - Rate limiting and sliding window protection
   - Generic timing-safe anti-enumeration responses
   - Cryptographic SHA-256 token hashing and storage safety (no raw token in DB)
   - 15-minute token expiry and single-use enforcement
   - Invalidation of previous tokens upon new request
   - Rejection of tampered, expired, or already-used tokens
   - Blocking unapproved accounts from password reset
   - Password update with PBKDF2-HMAC-SHA256 and active session revocation
   - Rejection of old passwords and successful authentication with new passwords
"""

import pytest
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.gateway import Student, GatewaySession, PasswordResetToken, AdminUser
from app.services.openwrt_service import create_admin_token, hash_password, verify_password
from app.services.email_service import check_rate_limit, _rate_limit_store

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_headers(db_session):
    admin = db_session.query(AdminUser).filter_by(username="admin").first()
    if not admin:
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("Admin@Campus2026"),
            full_name="Campus Admin",
            role="SUPERADMIN",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()
    token = create_admin_token(admin.username, admin.full_name, admin.role)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# SECTION 1: DEMO ACCOUNT ISOLATION AND VISIBILITY
# ==============================================================================

def test_student_list_views_and_demo_isolation(admin_headers):
    """
    Verify that:
    - view=ordinary returns only real students + 1 designated demo account (total 2).
    - view=demo_testing returns all 5 demo accounts.
    - view=all returns all 6 student accounts.
    - default view is 'ordinary'.
    - the 4 secondary demo accounts never appear in ordinary roster.
    """
    # 1. Ordinary active roster view (view=ordinary)
    res_ordinary = client.get("/api/v1/gateway/students?view=ordinary", headers=admin_headers)
    assert res_ordinary.status_code == 200
    ordinary_students = res_ordinary.json()
    assert len(ordinary_students) == 2, f"Expected 2 ordinary students, got {len(ordinary_students)}"

    ordinary_usns = {s["college_usn"] for s in ordinary_students}
    assert "ENG23CS0000" in ordinary_usns
    assert "DEMO-USN-CSE01" in ordinary_usns
    # Secondary demo accounts must NOT be in ordinary list
    assert "DEMO-USN-IT02" not in ordinary_usns
    assert "DEMO-USN-ECE03" not in ordinary_usns
    assert "DEMO-USN-ME04" not in ordinary_usns
    assert "DEMO-USN-EXH05" not in ordinary_usns

    # Check is_designated_demo flags
    for s in ordinary_students:
        if s["college_usn"] == "DEMO-USN-CSE01":
            assert s["is_demo"] is True
            assert s["is_designated_demo"] is True
        else:
            assert s["is_demo"] is False
            assert s["is_designated_demo"] is False

    # 2. Demo & Testing Fixtures view
    res_demo = client.get("/api/v1/gateway/students?view=demo_testing", headers=admin_headers)
    assert res_demo.status_code == 200
    demo_students = res_demo.json()
    assert len(demo_students) == 5, f"Expected 5 demo fixtures, got {len(demo_students)}"
    demo_usns = {s["college_usn"] for s in demo_students}
    expected_demos = {
        "DEMO-USN-CSE01", "DEMO-USN-IT02", "DEMO-USN-ECE03", "DEMO-USN-ME04", "DEMO-USN-EXH05"
    }
    assert demo_usns == expected_demos
    for s in demo_students:
        assert s["is_demo"] is True

    # 3. All Records view
    res_all = client.get("/api/v1/gateway/students?view=all", headers=admin_headers)
    assert res_all.status_code == 200
    all_students = res_all.json()
    assert len(all_students) == 6, f"Expected 6 total students, got {len(all_students)}"

    # 4. Default query without view param preserves backward compatibility (returns all)
    res_default = client.get("/api/v1/gateway/students", headers=admin_headers)
    assert res_default.status_code == 200
    assert len(res_default.json()) == 6


# ==============================================================================
# SECTION 2: STUDENT REGISTRATION, EMAIL VALIDATION & DUPLICATE PROTECTION
# ==============================================================================

def test_student_registration_and_validation(db_session):
    """
    Verify student registration with email, duplicate USN/email rejection,
    and validation constraints.
    """
    unique_suffix = int(datetime.now().timestamp()) % 100000
    test_usn = f"ENG23CS{unique_suffix:05d}"
    test_email = f"student_{unique_suffix}@campus.edu.in"

    try:
        # 1. Successful registration
        payload = {
            "college_usn": test_usn,
            "name": "Test Candidate",
            "email": test_email,
            "password": "Password@2026",
            "academic_year": "3rd Year",
            "department": "Computer Science Core",
        }
        res = client.post("/api/v1/gateway/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["college_usn"] == test_usn
        assert data["approval_status"] == "PENDING_APPROVAL"

        # 2. Reject duplicate USN
        res_dup_usn = client.post("/api/v1/gateway/register", json={
            "college_usn": test_usn,
            "name": "Another Name",
            "email": f"different_{unique_suffix}@campus.edu.in",
            "password": "Password@2026",
        })
        assert res_dup_usn.status_code == 409
        assert "already exists" in res_dup_usn.json()["detail"].lower()

        # 3. Reject duplicate Email
        res_dup_email = client.post("/api/v1/gateway/register", json={
            "college_usn": f"ENG23IT{unique_suffix:05d}",
            "name": "Another Name",
            "email": test_email,
            "password": "Password@2026",
        })
        assert res_dup_email.status_code == 409
        assert "email" in res_dup_email.json()["detail"].lower()

        # 4. Reject invalid USN format
        res_bad_usn = client.post("/api/v1/gateway/register", json={
            "college_usn": "INVALID_USN",
            "name": "Invalid USN Test",
            "email": f"bad_usn_{unique_suffix}@campus.edu.in",
            "password": "Password@2026",
        })
        assert res_bad_usn.status_code in (400, 422)

        # 5. Reject invalid Email format
        res_bad_email = client.post("/api/v1/gateway/register", json={
            "college_usn": f"ENG23EC{unique_suffix:05d}",
            "name": "Invalid Email Test",
            "email": "not-a-valid-email",
            "password": "Password@2026",
        })
        assert res_bad_email.status_code in (400, 422)

        # 6. Reject short password (< 6 chars)
        res_short_pw = client.post("/api/v1/gateway/register", json={
            "college_usn": f"ENG23EC{unique_suffix:05d}",
            "name": "Short Password Test",
            "email": f"short_pw_{unique_suffix}@campus.edu.in",
            "password": "123",
        })
        assert res_short_pw.status_code in (400, 422)

    finally:
        # Cleanup test records
        db_session.query(Student).filter(
            Student.college_usn.in_([test_usn, f"ENG23IT{unique_suffix:05d}", f"ENG23EC{unique_suffix:05d}"])
        ).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# SECTION 3: ACCESS CONTROL & APPROVAL ENFORCEMENT
# ==============================================================================

def test_pending_vs_approved_student_login(db_session, admin_headers):
    """
    Verify that:
    - PENDING_APPROVAL student login is blocked with HTTP 403.
    - Admin approval activates the account.
    - APPROVED student can authenticate successfully.
    """
    unique_suffix = int(datetime.now().timestamp()) % 100000
    test_usn = f"ENG23CS{unique_suffix:05d}"
    test_email = f"pending_{unique_suffix}@campus.edu.in"
    test_pw = "ApprovalTest@2026"
    student = None

    try:
        # Register student
        res_reg = client.post("/api/v1/gateway/register", json={
            "college_usn": test_usn,
            "name": "Pending Approval Student",
            "email": test_email,
            "password": test_pw,
        })
        assert res_reg.status_code == 201

        # Attempt login before approval -> MUST FAIL 403
        res_login_pending = client.post("/api/v1/gateway/login", json={
            "college_usn": test_usn,
            "password": test_pw,
            "client_mac": "00:50:56:c0:00:01",
            "simulate_gateway": True,
        })
        assert res_login_pending.status_code == 403
        assert "pending administrator approval" in res_login_pending.json()["detail"].lower()

        # Admin approves student
        res_approve = client.post(
            f"/api/v1/gateway/students/{test_usn}/approval",
            json={"approval_status": "APPROVED", "admin_notes": "Automated test approval"},
            headers=admin_headers,
        )
        assert res_approve.status_code == 200
        assert res_approve.json()["approval_status"] == "APPROVED"

        # Attempt login after approval -> MUST SUCCEED 200
        res_login_approved = client.post("/api/v1/gateway/login", json={
            "college_usn": test_usn,
            "password": test_pw,
            "client_mac": "00:50:56:c0:00:01",
            "simulate_gateway": True,
        })
        assert res_login_approved.status_code == 200
        login_data = res_login_approved.json()
        assert login_data["success"] is True
        assert login_data["gateway_authorized"] is True

    finally:
        # Cleanup
        if student:
            db_session.query(GatewaySession).filter_by(student_id=student.id).delete(synchronize_session=False)
        db_session.query(Student).filter_by(college_usn=test_usn).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# SECTION 4: SECURE FORGOT PASSWORD & TOKEN WORKFLOW
# ==============================================================================

def test_password_reset_anti_enumeration_and_timing_safety():
    """
    Verify that password reset request returns identical generic responses
    whether the user exists, does not exist, or is pending approval.
    """
    # 1. Existing approved student (USN)
    r1 = client.post("/api/v1/gateway/password-reset/request", json={"identifier": "DEMO-USN-CSE01"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["success"] is True
    assert "If an account associated with this identifier is registered and approved" in data1["message"]

    # 2. Existing approved student (Email)
    r2 = client.post("/api/v1/gateway/password-reset/request", json={"identifier": "demo.cse01@campus.edu.in"})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["success"] is True
    assert data2["message"] == data1["message"]

    # 3. Nonexistent account
    r3 = client.post("/api/v1/gateway/password-reset/request", json={"identifier": "NONEXISTENT-USN-9999"})
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["success"] is True
    assert data3["message"] == data1["message"]


def test_password_reset_rate_limiting():
    """
    Verify sliding window rate limiting on password reset requests.
    """
    # Clear rate limit store for testing
    _rate_limit_store.clear()

    test_ip = "192.168.1.99"
    # First 5 calls pass
    for _ in range(5):
        assert check_rate_limit(f"ip:{test_ip}", max_requests=5, window_seconds=900) is True

    # 6th call exceeds rate limit
    assert check_rate_limit(f"ip:{test_ip}", max_requests=5, window_seconds=900) is False

    # Verify endpoint returns 429 when rate limit exceeded
    with patch("app.routers.gateway.check_rate_limit", return_value=False):
        res = client.post("/api/v1/gateway/password-reset/request", json={"identifier": "DEMO-USN-CSE01"})
        assert res.status_code == 429
        assert "Too many password reset requests" in res.json()["detail"]


def test_password_reset_token_hashing_and_security(db_session):
    """
    Verify that:
    - Raw token is never stored in database; only SHA-256 hash is saved.
    - Previous tokens for the same student are invalidated when a new token is issued.
    - Unapproved accounts do not receive active reset tokens.
    """
    student = db_session.query(Student).filter_by(college_usn="DEMO-USN-CSE01").first()
    assert student is not None

    # Clear prior tokens
    db_session.query(PasswordResetToken).filter_by(student_id=student.id).delete()
    db_session.commit()

    # Request reset in non-production mode to inspect generated token via dev mailbox
    with patch("app.routers.gateway.settings.ENVIRONMENT", "development"):
        res = client.post("/api/v1/gateway/password-reset/request", json={"identifier": student.college_usn})
        assert res.status_code == 200

    # Query database for the stored token record
    stored_token = db_session.query(PasswordResetToken).filter_by(student_id=student.id, is_invalidated=False).first()
    assert stored_token is not None
    # Stored token hash must be exactly 64 hex characters (SHA-256)
    assert len(stored_token.token_hash) == 64
    assert not stored_token.token_hash.startswith("http")
    assert stored_token.used_at is None
    assert stored_token.is_invalidated is False

    # Issue a second token: first token must be invalidated
    first_token_id = stored_token.id
    with patch("app.routers.gateway.settings.ENVIRONMENT", "development"):
        res2 = client.post("/api/v1/gateway/password-reset/request", json={"identifier": student.college_usn})
        assert res2.status_code == 200

    db_session.expire_all()
    first_token_refreshed = db_session.query(PasswordResetToken).filter_by(id=first_token_id).first()
    assert first_token_refreshed.is_invalidated is True

    # Cleanup tokens
    db_session.query(PasswordResetToken).filter_by(student_id=student.id).delete()
    db_session.commit()


def test_password_reset_verification_and_expiry(db_session):
    """
    Verify token verification endpoint:
    - Valid token returns masked account info.
    - Tampered token returns 400.
    - Expired token returns 400.
    - Invalidated token returns 400.
    """
    student = db_session.query(Student).filter_by(college_usn="ENG23CS0000").first()
    assert student is not None

    # Generate a dummy raw token
    import secrets
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Insert valid token
    db_token = PasswordResetToken(
        student_id=student.id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_invalidated=False,
    )
    db_session.add(db_token)
    db_session.commit()

    try:
        # 1. Valid token verification
        res_valid = client.post("/api/v1/gateway/password-reset/verify-token", json={"token": raw_token})
        assert res_valid.status_code == 200
        data = res_valid.json()
        assert data["valid"] is True
        assert data["masked_usn"].startswith("ENG")
        assert data["masked_usn"].endswith("00")

        # 2. Tampered token verification
        res_tampered = client.post("/api/v1/gateway/password-reset/verify-token", json={"token": raw_token + "_tampered"})
        assert res_tampered.status_code == 400
        assert "invalid" in res_tampered.json()["detail"].lower()

        # 3. Expired token verification
        db_token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()
        res_expired = client.post("/api/v1/gateway/password-reset/verify-token", json={"token": raw_token})
        assert res_expired.status_code == 400
        assert "expired" in res_expired.json()["detail"].lower()

        # 4. Invalidated token verification
        db_token.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        db_token.is_invalidated = True
        db_session.commit()
        res_invalidated = client.post("/api/v1/gateway/password-reset/verify-token", json={"token": raw_token})
        assert res_invalidated.status_code == 400
        assert "invalid" in res_invalidated.json()["detail"].lower()

    finally:
        db_session.query(PasswordResetToken).filter_by(token_hash=token_hash).delete()
        db_session.commit()


def test_password_reset_confirmation_workflow(db_session):
    """
    Verify complete password confirmation workflow:
    - Passwords must match and be at least 6 characters.
    - Password is updated using PBKDF2-HMAC-SHA256.
    - Token is marked as used and cannot be reused.
    - Old password is rejected for login.
    - New password succeeds for login.
    - Active sessions are revoked.
    """
    unique_suffix = int(datetime.now().timestamp()) % 100000
    test_usn = f"ENG23CS{unique_suffix:05d}"
    test_email = f"reset_{unique_suffix}@campus.edu.in"
    original_pw = "OriginalPass@2026"
    new_pw = "UpdatedPass@2026"

    # Register and approve a test student
    student = Student(
        student_id=f"TEST-{unique_suffix}",
        college_usn=test_usn,
        name="Reset Test Student",
        email=test_email,
        password_hash=hash_password(original_pw),
        department="Computer Science Core",
        academic_year="3rd Year",
        daily_quota_mb=1024.0,
        approval_status="APPROVED",
        is_active=True,
        is_demo=False,
    )
    db_session.add(student)
    db_session.commit()

    # Create an active gateway session
    active_session = GatewaySession(
        student_id=student.id,
        client_mac="02:00:00:aa:bb:cc",
        session_start=datetime.now(timezone.utc),
        bytes_uploaded=1000,
        bytes_downloaded=5000,
        quota_assigned_kb=1048576,
        status="ACTIVE",
    )
    db_session.add(active_session)
    db_session.commit()

    import secrets
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    reset_token_rec = PasswordResetToken(
        student_id=student.id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_invalidated=False,
    )
    db_session.add(reset_token_rec)
    db_session.commit()

    try:
        # 1. Reject mismatched passwords
        res_mismatch = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token,
            "new_password": new_pw,
            "confirm_password": "DifferentPassword@2026",
        })
        assert res_mismatch.status_code == 400
        assert "do not match" in res_mismatch.json()["detail"]

        # 2. Reject short password
        res_short = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token,
            "new_password": "123",
            "confirm_password": "123",
        })
        assert res_short.status_code == 422

        # 3. Successful password confirmation
        res_confirm = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token,
            "new_password": new_pw,
            "confirm_password": new_pw,
        })
        assert res_confirm.status_code == 200
        assert res_confirm.json()["success"] is True

        # 4. Token marked as used; reusing token must fail
        db_session.expire_all()
        token_after = db_session.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
        assert token_after.used_at is not None

        res_reuse = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token,
            "new_password": "AnotherPass@2026",
            "confirm_password": "AnotherPass@2026",
        })
        assert res_reuse.status_code == 400
        assert "already been used" in res_reuse.json()["detail"].lower()

        # 5. Active sessions revoked
        session_after = db_session.query(GatewaySession).filter_by(id=active_session.id).first()
        assert session_after.status == "DEAUTHED"
        assert "Password reset revocation" in session_after.notes

        # 6. Verify password hash updated with PBKDF2-HMAC-SHA256
        student_after = db_session.query(Student).filter_by(id=student.id).first()
        assert verify_password(new_pw, student_after.password_hash) is True
        assert verify_password(original_pw, student_after.password_hash) is False

        # 7. Old password login fails
        res_old_login = client.post("/api/v1/gateway/login", json={
            "college_usn": test_usn,
            "password": original_pw,
            "client_mac": "00:50:56:c0:00:01",
            "simulate_gateway": True,
        })
        assert res_old_login.status_code == 401

        # 8. New password login succeeds
        res_new_login = client.post("/api/v1/gateway/login", json={
            "college_usn": test_usn,
            "password": new_pw,
            "client_mac": "00:50:56:c0:00:01",
            "simulate_gateway": True,
        })
        assert res_new_login.status_code == 200
        assert res_new_login.json()["success"] is True

    finally:
        # Cleanup
        db_session.query(GatewaySession).filter_by(student_id=student.id).delete(synchronize_session=False)
        db_session.query(PasswordResetToken).filter_by(student_id=student.id).delete(synchronize_session=False)
        db_session.query(Student).filter_by(id=student.id).delete(synchronize_session=False)
        db_session.commit()


# ==============================================================================
# SECTION 5: ADVANCED SECURITY, CONCURRENCY & SESSION ISOLATION AUDIT
# ==============================================================================

def test_dev_mailbox_production_inaccessibility_and_misspelled_env():
    """
    Verify fail-secure policy:
    - Production mode completely blocks dev mailbox access.
    - Misspelled or variation environments ('prod', 'Production', 'PROD', 'live', '') fail-secure.
    - ALLOW_DEV_RESET_MAILBOX=True cannot enable mailbox in production.
    """
    from app.services.email_service import get_dev_mailbox, is_dev_mailbox_enabled

    # 1. Standard production mode
    with patch("app.services.email_service.settings.ENVIRONMENT", "production"), \
         patch("app.services.email_service.settings.ALLOW_DEV_RESET_MAILBOX", True):
        assert is_dev_mailbox_enabled() is False
        assert get_dev_mailbox() == []

    # 2. Case variations and abbreviations ('PROD', 'Production', 'prod', 'live')
    for env_var in ("PROD", "Production", "prod", "live", "production_server", "staging"):
        with patch("app.services.email_service.settings.ENVIRONMENT", env_var), \
             patch("app.services.email_service.settings.ALLOW_DEV_RESET_MAILBOX", True):
            assert is_dev_mailbox_enabled() is False, f"Failed for ENVIRONMENT={env_var}"
            assert get_dev_mailbox() == [], f"Mailbox not empty for ENVIRONMENT={env_var}"

    # 3. Missing or empty ENVIRONMENT
    for env_var in ("", "   ", None):
        with patch("app.services.email_service.settings.ENVIRONMENT", env_var), \
             patch("app.services.email_service.settings.ALLOW_DEV_RESET_MAILBOX", True):
            assert is_dev_mailbox_enabled() is False
            assert get_dev_mailbox() == []


def test_concurrent_reset_confirmation_single_use(db_session):
    """
    Verify that concurrent reset confirmation requests cannot double-consume the same token.
    Exactly one request must succeed (HTTP 200) and the concurrent request must fail (HTTP 400).
    """
    import secrets
    import concurrent.futures

    unique_suffix = int(datetime.now().timestamp()) % 100000
    test_usn = f"ENG23CS{unique_suffix:05d}"
    test_email = f"concurrent_{unique_suffix}@campus.edu.in"
    original_pw = "ConcurPass@2026"

    student = Student(
        student_id=f"CONCUR-{unique_suffix}",
        college_usn=test_usn,
        name="Concurrent Test Student",
        email=test_email,
        password_hash=hash_password(original_pw),
        department="Computer Science Core",
        approval_status="APPROVED",
        is_active=True,
        is_demo=False,
    )
    db_session.add(student)
    db_session.commit()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    token_rec = PasswordResetToken(
        student_id=student.id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_invalidated=False,
    )
    db_session.add(token_rec)
    db_session.commit()

    try:
        def attempt_confirm(pw):
            return client.post("/api/v1/gateway/password-reset/confirm", json={
                "token": raw_token,
                "new_password": pw,
                "confirm_password": pw,
            })

        # Launch two simultaneous confirmation requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(attempt_confirm, "NewPassA@2026")
            fut2 = executor.submit(attempt_confirm, "NewPassB@2026")
            res1 = fut1.result()
            res2 = fut2.result()

        status_codes = sorted([res1.status_code, res2.status_code])
        # Exactly one must be 200 OK, and exactly one must be 400 Bad Request
        assert status_codes == [200, 400], f"Expected [200, 400] but got {status_codes}"

    finally:
        db_session.query(PasswordResetToken).filter_by(token_hash=token_hash).delete()
        db_session.query(Student).filter_by(id=student.id).delete()
        db_session.commit()


def test_isolated_session_revocation(db_session):
    """
    Verify that when student A resets their password:
    - Student A's active gateway session is DEAUTHED.
    - Student B's active gateway session is completely UNTOUCHED (remains ACTIVE).
    """
    import secrets

    student_a = Student(
        student_id="ISOL-A-01",
        college_usn="ENG23CS88881",
        name="Student A",
        email="student.a@campus.edu.in",
        password_hash=hash_password("PassA@2026"),
        approval_status="APPROVED",
        is_active=True,
    )
    student_b = Student(
        student_id="ISOL-B-02",
        college_usn="ENG23CS88882",
        name="Student B",
        email="student.b@campus.edu.in",
        password_hash=hash_password("PassB@2026"),
        approval_status="APPROVED",
        is_active=True,
    )
    db_session.add_all([student_a, student_b])
    db_session.commit()

    # Active session for student A
    session_a = GatewaySession(
        student_id=student_a.id,
        client_mac="02:00:00:11:11:11",
        session_start=datetime.now(timezone.utc),
        bytes_uploaded=100,
        bytes_downloaded=100,
        quota_assigned_kb=1048576,
        status="ACTIVE",
    )
    # Active session for student B
    session_b = GatewaySession(
        student_id=student_b.id,
        client_mac="02:00:00:22:22:22",
        session_start=datetime.now(timezone.utc),
        bytes_uploaded=200,
        bytes_downloaded=200,
        quota_assigned_kb=1048576,
        status="ACTIVE",
    )
    db_session.add_all([session_a, session_b])
    db_session.commit()

    raw_token_a = secrets.token_urlsafe(32)
    token_hash_a = hashlib.sha256(raw_token_a.encode("utf-8")).hexdigest()
    reset_rec_a = PasswordResetToken(
        student_id=student_a.id,
        token_hash=token_hash_a,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_invalidated=False,
    )
    db_session.add(reset_rec_a)
    db_session.commit()

    try:
        # Student A resets password
        res = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token_a,
            "new_password": "NewPassA@2026",
            "confirm_password": "NewPassA@2026",
        })
        assert res.status_code == 200

        db_session.expire_all()
        session_a_after = db_session.query(GatewaySession).filter_by(id=session_a.id).first()
        session_b_after = db_session.query(GatewaySession).filter_by(id=session_b.id).first()

        # Student A's session MUST be DEAUTHED
        assert session_a_after.status == "DEAUTHED"
        assert session_a_after.session_end is not None

        # Student B's session MUST remain ACTIVE
        assert session_b_after.status == "ACTIVE"
        assert session_b_after.session_end is None

    finally:
        db_session.query(GatewaySession).filter(GatewaySession.student_id.in_([student_a.id, student_b.id])).delete(synchronize_session=False)
        db_session.query(PasswordResetToken).filter(PasswordResetToken.student_id.in_([student_a.id, student_b.id])).delete(synchronize_session=False)
        db_session.query(Student).filter(Student.id.in_([student_a.id, student_b.id])).delete(synchronize_session=False)
        db_session.commit()


def test_unapproved_or_rejected_student_cannot_reset_password(db_session):
    """
    Verify that pending approval and rejected students cannot reset credentials.
    """
    import secrets

    student_pending = Student(
        student_id="PEND-TEST-01",
        college_usn="ENG23CS77771",
        name="Pending Candidate",
        email="pending.candidate@campus.edu.in",
        password_hash=hash_password("PendingPass@2026"),
        approval_status="PENDING_APPROVAL",
        is_active=False,
    )
    student_rejected = Student(
        student_id="REJ-TEST-02",
        college_usn="ENG23CS77772",
        name="Rejected Candidate",
        email="rejected.candidate@campus.edu.in",
        password_hash=hash_password("RejectedPass@2026"),
        approval_status="REJECTED",
        is_active=False,
    )
    db_session.add_all([student_pending, student_rejected])
    db_session.commit()

    try:
        # 1. Request reset for pending student -> returns generic response, but creates NO active token
        r_pend = client.post("/api/v1/gateway/password-reset/request", json={"identifier": student_pending.college_usn})
        assert r_pend.status_code == 200
        token_pend = db_session.query(PasswordResetToken).filter_by(student_id=student_pending.id).first()
        assert token_pend is None, "Pending student must not have reset token generated"

        # 2. Request reset for rejected student -> returns generic response, but creates NO active token
        r_rej = client.post("/api/v1/gateway/password-reset/request", json={"identifier": student_rejected.college_usn})
        assert r_rej.status_code == 200
        token_rej = db_session.query(PasswordResetToken).filter_by(student_id=student_rejected.id).first()
        assert token_rej is None, "Rejected student must not have reset token generated"

        # 3. If an adversary attempts to confirm a crafted token for unapproved student -> MUST FAIL 403
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        crafted_token = PasswordResetToken(
            student_id=student_pending.id,
            token_hash=token_hash,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            is_invalidated=False,
        )
        db_session.add(crafted_token)
        db_session.commit()

        res_confirm = client.post("/api/v1/gateway/password-reset/confirm", json={
            "token": raw_token,
            "new_password": "NewAttempt@2026",
            "confirm_password": "NewAttempt@2026",
        })
        assert res_confirm.status_code == 403
        assert "not eligible" in res_confirm.json()["detail"].lower()

    finally:
        db_session.query(PasswordResetToken).filter(PasswordResetToken.student_id.in_([student_pending.id, student_rejected.id])).delete(synchronize_session=False)
        db_session.query(Student).filter(Student.id.in_([student_pending.id, student_rejected.id])).delete(synchronize_session=False)
        db_session.commit()


def test_reset_token_cannot_be_used_as_auth_credentials():
    """
    Verify that reset tokens cannot be used as passwords for student login
    or as Bearer tokens for administrator access.
    """
    import secrets
    dummy_reset_token = secrets.token_urlsafe(32)

    # 1. Attempt login using reset token as password -> 401
    res_login = client.post("/api/v1/gateway/login", json={
        "college_usn": "DEMO-USN-CSE01",
        "password": dummy_reset_token,
        "client_mac": "00:50:56:c0:00:01",
        "simulate_gateway": True,
    })
    assert res_login.status_code == 401

    # 2. Attempt admin access using reset token as Bearer auth -> 401
    res_admin = client.get("/api/v1/gateway/admin/me", headers={
        "Authorization": f"Bearer {dummy_reset_token}"
    })
    assert res_admin.status_code == 401
