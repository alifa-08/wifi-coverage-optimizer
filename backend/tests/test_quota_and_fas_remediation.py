"""
Phase 5 Remediation Test Suite — Quota Accounting & FAS Redirect Security.

Covers the 12 required test scenarios:
 1. Repeated polling of unchanged counter (idempotent delta tracking, no double-counting).
 2. Multi-session accumulation (Session 1 [100 MiB] + Session 2 [40 MiB] -> 140 MiB).
 3. Repeated polling of second session (preserves 140 MiB, no drift).
 4. Router counter reset / rollover (preserves usage, clamps delta to 0).
 5. Session disappearance before final poll (preserves last-known bytes, marks LAST_KNOWN_INCOMPLETE).
 6. MAC reassignment (supersedes prior session, preserves Student A's usage, gives clean session to Student B).
 7. Untrusted gatewayaddress rejected (rejects external hostnames, unexpected ports, path components).
 8. Query parameter gateway override blocked (portal landing and form submit refuse evil.com).
 9. Malicious authdir sanitized (rejects path traversal, falls back to opennds_auth).
10. Unsafe redirect URLs rejected (blocks javascript:, data:, file:, and CRLF injection).
11. Legitimate FAS URL construction (constructs valid OpenNDS Level 1 redirect URL).
12. System compatibility with existing features (registration, approval, login, quota blocks).

SAFETY GUARANTEE:
Executes strictly against an isolated in-memory SQLite database (StaticPool) and mocks.
The production database is never touched or modified.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.gateway import Student, GatewaySession, AdminUser, seed_default_students
from app.services.openwrt_service import (
    get_trusted_gateway_destination,
    sanitize_authdir,
    sanitize_redirect_url,
    build_opennds_auth_url,
    compute_fas_token,
    hash_password,
    verify_password,
    create_admin_token,
    BYTES_PER_MIB
)

# Set up isolated in-memory SQLite database with StaticPool for thread-safety and persistence across requests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_isolated_db():
    """Seed and clean up isolated in-memory database between tests."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        seed_default_students(db)
        admin = AdminUser(
            username="admin_test",
            password_hash=hash_password("adminpass123"),
            full_name="Test Administrator",
            role="SUPERADMIN",
            is_active=True
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()
    yield
    app.dependency_overrides.clear()


# =====================================================================
# Scenario 1: Repeated Polling of Unchanged Counter (No Double-Counting)
# =====================================================================
def test_repeated_polling_unchanged_counter():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0101",
            student_id="CS-0101",
            name="Alice Walker",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        session = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:01",
            client_ip="192.168.214.101",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(session)
        db.commit()
    finally:
        db.close()

    mock_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:01": {
                "ip": "192.168.214.101",
                "upload_bytes": 10 * BYTES_PER_MIB,
                "download_bytes": 40 * BYTES_PER_MIB,
                "state": "authenticated",
                "session_start": int(datetime.utcnow().timestamp()),
                "session_end": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
                "upload_quota": 200000,
                "download_quota": 800000
            }
        }
    }

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_clients):
        # First poll: 50 MiB reported
        res1 = client.get("/api/v1/gateway/sessions")
        assert res1.status_code == 200

        db = TestSessionLocal()
        s1 = db.query(Student).filter(Student.college_usn == "ENG23CS0101").first()
        sess1 = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:01").first()
        assert s1.used_quota_mb == 50.0
        assert sess1.bytes_uploaded == 10 * BYTES_PER_MIB
        assert sess1.bytes_downloaded == 40 * BYTES_PER_MIB
        db.close()

        # Second poll: Same 50 MiB reported
        res2 = client.get("/api/v1/gateway/sessions")
        assert res2.status_code == 200

        db = TestSessionLocal()
        s2 = db.query(Student).filter(Student.college_usn == "ENG23CS0101").first()
        assert s2.used_quota_mb == 50.0, "Repeated poll must NOT double-count traffic"
        db.close()


# =====================================================================
# Scenario 2: Multi-Session Accumulation (100 MiB + 40 MiB -> 140 MiB)
# =====================================================================
def test_multi_session_accumulation():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0102",
            student_id="CS-0102",
            name="Bob Martin",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Session 1 on MAC 1
        sess1 = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:02",
            client_ip="192.168.214.102",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(sess1)
        db.commit()
    finally:
        db.close()

    mock_sess1_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:02": {
                "ip": "192.168.214.102",
                "upload_bytes": 30 * BYTES_PER_MIB,
                "download_bytes": 70 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_sess1_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0102").first()
    assert st.used_quota_mb == 100.0, "Session 1 should record 100 MiB"

    # End Session 1
    sess1 = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:02").first()
    sess1.status = "EXPIRED"
    sess1.session_end = datetime.utcnow()

    # Start Session 2 on MAC 2 (new session starts with counters at 0)
    sess2 = GatewaySession(
        student_id=st.id,
        client_mac="02:00:00:00:01:03",
        client_ip="192.168.214.103",
        session_start=datetime.utcnow(),
        quota_assigned_kb=(1024.0 - 100.0) * 1024,
        bytes_uploaded=0.0,
        bytes_downloaded=0.0,
        status="ACTIVE"
    )
    db.add(sess2)
    db.commit()
    db.close()

    # Session 2 consumes 40 MiB
    mock_sess2_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:03": {
                "ip": "192.168.214.103",
                "upload_bytes": 10 * BYTES_PER_MIB,
                "download_bytes": 30 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_sess2_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0102").first()
    assert st.used_quota_mb == 140.0, f"Session 1 (100) + Session 2 (40) must accumulate to 140 MiB, got {st.used_quota_mb}"
    db.close()


# =====================================================================
# Scenario 3: Repeated Polling of Second Session (Stays 140 MiB)
# =====================================================================
def test_repeated_polling_second_session():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0103",
            student_id="CS-0103",
            name="Charlie Day",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=140.0,  # Prior cumulative usage
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess2 = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:04",
            client_ip="192.168.214.104",
            session_start=datetime.utcnow(),
            quota_assigned_kb=924.0 * 1024,
            bytes_uploaded=10.0 * BYTES_PER_MIB,
            bytes_downloaded=30.0 * BYTES_PER_MIB,
            status="ACTIVE"
        )
        db.add(sess2)
        db.commit()
    finally:
        db.close()

    mock_sess2_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:04": {
                "ip": "192.168.214.104",
                "upload_bytes": 10 * BYTES_PER_MIB,
                "download_bytes": 30 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_sess2_clients):
        res1 = client.get("/api/v1/gateway/sessions")
        assert res1.status_code == 200
        res2 = client.get("/api/v1/gateway/sessions")
        assert res2.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0103").first()
    assert st.used_quota_mb == 140.0, "Repeated polls of Session 2 must strictly remain at 140.0 MiB"
    db.close()


# =====================================================================
# Scenario 4: Router Counter Reset Preserves Usage
# =====================================================================
def test_router_counter_reset_preserves_usage():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0104",
            student_id="CS-0104",
            name="Diana Prince",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=140.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:05",
            client_ip="192.168.214.105",
            session_start=datetime.utcnow(),
            quota_assigned_kb=884.0 * 1024,
            bytes_uploaded=10.0 * BYTES_PER_MIB,
            bytes_downloaded=30.0 * BYTES_PER_MIB,
            status="ACTIVE"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Router restarts/resets counters to 0
    mock_reset_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:05": {
                "ip": "192.168.214.105",
                "upload_bytes": 0,
                "download_bytes": 0,
                "state": "authenticated"
            }
        }
    }

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_reset_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0104").first()
    sess_after = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:05").first()
    assert st.used_quota_mb == 140.0, "Used quota must not drop when router counters reset to 0"
    assert sess_after.bytes_uploaded == 10.0 * BYTES_PER_MIB, "Monotonic max should preserve recorded bytes"
    assert sess_after.bytes_downloaded == 30.0 * BYTES_PER_MIB
    db.close()


# =====================================================================
# Scenario 5: Session Disappearance Before Final Poll
# =====================================================================
def test_session_disappearance_before_final_poll():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0105",
            student_id="CS-0105",
            name="Evan Wright",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=25.0,
            session_timeout_mins=1,  # Short timeout for reconciliation test
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:06",
            client_ip="192.168.214.106",
            session_start=datetime.utcnow() - timedelta(minutes=5),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=5.0 * BYTES_PER_MIB,
            bytes_downloaded=20.0 * BYTES_PER_MIB,
            status="ACTIVE",
            notes="Active FAS session"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Client disappeared from OpenNDS client list
    mock_empty_clients = {"client_list_length": 0, "clients": {}}

    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=mock_empty_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    reconciled_sess = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:06").first()
    assert reconciled_sess.status == "EXPIRED"
    assert "Incomplete traffic accounting" in (reconciled_sess.notes or "")
    assert reconciled_sess.traffic_completeness == "LAST_KNOWN_INCOMPLETE"
    assert reconciled_sess.bytes_uploaded == 5.0 * BYTES_PER_MIB
    assert reconciled_sess.bytes_downloaded == 20.0 * BYTES_PER_MIB

    # Verify JSON serialization includes traffic_completeness
    history_item = next((item for item in res.json()["recent_history"] if item["client_mac"] == "02:00:00:00:01:06"), None)
    assert history_item is not None
    assert history_item["traffic_completeness"] == "LAST_KNOWN_INCOMPLETE"
    db.close()


# =====================================================================
# Scenario 6: MAC Reassignment Preserves Student A's Usage
# =====================================================================
def test_mac_reassignment_preserves_previous_student():
    db = TestSessionLocal()
    try:
        student_a = Student(
            college_usn="ENG23CS0106A",
            student_id="CS-0106A",
            name="Student A",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("PasswordA1!"),
            daily_quota_mb=1024.0,
            used_quota_mb=100.0,
            is_active=True
        )
        student_b = Student(
            college_usn="ENG23CS0106B",
            student_id="CS-0106B",
            name="Student B",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("PasswordB1!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add_all([student_a, student_b])
        db.commit()
        db.refresh(student_a)
        db.refresh(student_b)

        # Existing active session for Student A on shared MAC
        shared_mac = "02:00:00:00:01:07"
        sess_a = GatewaySession(
            student_id=student_a.id,
            client_mac=shared_mac,
            client_ip="192.168.214.107",
            session_start=datetime.utcnow() - timedelta(hours=1),
            quota_assigned_kb=924.0 * 1024,
            bytes_uploaded=30.0 * BYTES_PER_MIB,
            bytes_downloaded=70.0 * BYTES_PER_MIB,
            status="ACTIVE"
        )
        db.add(sess_a)
        db.commit()
    finally:
        db.close()

    # Student B logs in from the same physical device MAC
    login_payload = {
        "college_usn": "ENG23CS0106B",
        "password": "PasswordB1!",
        "client_mac": shared_mac,
        "client_ip": "192.168.214.107",
        "simulate_gateway": True
    }
    res = client.post("/api/v1/gateway/login", json=login_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True

    db = TestSessionLocal()
    st_a = db.query(Student).filter(Student.college_usn == "ENG23CS0106A").first()
    st_b = db.query(Student).filter(Student.college_usn == "ENG23CS0106B").first()
    assert st_a.used_quota_mb == 100.0, "Student A usage must be preserved"
    assert st_b.used_quota_mb == 0.0, "Student B starts with clean 0.0 usage"

    # Prior session for Student A must be marked SUPERSEDED
    old_sess = db.query(GatewaySession).filter(
        GatewaySession.student_id == st_a.id,
        GatewaySession.client_mac == shared_mac
    ).first()
    assert old_sess.status == "SUPERSEDED"

    # New active session exists for Student B
    new_sess = db.query(GatewaySession).filter(
        GatewaySession.student_id == st_b.id,
        GatewaySession.client_mac == shared_mac
    ).first()
    assert new_sess.status == "ACTIVE"
    db.close()


# =====================================================================
# Scenario 7: Untrusted Gateway Destination Rejected
# =====================================================================
def test_untrusted_gatewayaddress_rejected():
    trusted = f"{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}"

    # External hostname
    assert get_trusted_gateway_destination("evil.com:8080") == trusted
    assert get_trusted_gateway_destination("http://attacker.org:2050") == trusted
    assert get_trusted_gateway_destination("https://malicious.net/opennds_auth") == trusted

    # Unexpected port on correct host
    assert get_trusted_gateway_destination(f"{settings.OPENWRT_HOST}:9999") == trusted
    assert get_trusted_gateway_destination(f"{settings.OPENWRT_HOST}:22") == trusted

    # Unexpected IP
    assert get_trusted_gateway_destination("192.168.1.1:2050") == trusted

    # None or empty
    assert get_trusted_gateway_destination(None) == trusted
    assert get_trusted_gateway_destination("") == trusted

    # Legitimate configured address
    assert get_trusted_gateway_destination(trusted) == trusted


# =====================================================================
# Scenario 8: Query Parameter Gateway Override Blocked
# =====================================================================
def test_query_parameter_gateway_override_blocked():
    # Attempting to override gatewayaddress via GET query parameter
    res = client.get("/api/v1/gateway/portal?gatewayaddress=evil.com:8080&format=json")
    assert res.status_code == 200
    data = res.json()
    assert "evil.com" not in data["gatewayaddress"]
    assert "evil.com" not in data["authaction"]
    assert data["gatewayaddress"] == f"{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}"

    # Form submit attempt to override gatewayaddress
    db = TestSessionLocal()
    try:
        st = Student(
            college_usn="ENG23CS0108",
            student_id="CS-0108",
            name="Grace Hopper",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("ValidPass123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(st)
        db.commit()
    finally:
        db.close()

    with patch("app.routers.gateway.gateway_service.authorize_client", return_value=(True, 150000, 850000)):
        submit_data = {
            "college_usn": "ENG23CS0108",
            "password": "ValidPass123!",
            "client_mac": "02:00:00:00:01:08",
            "gatewayaddress": "evil.com:8080",
            "hid": "test_hid_hash"
        }
        res_submit = client.post("/api/v1/gateway/portal/submit", data=submit_data, follow_redirects=False)
        assert res_submit.status_code == 303
        redir_target = res_submit.headers.get("location")
        assert "evil.com" not in redir_target
        assert f"{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}" in redir_target


# =====================================================================
# Scenario 9: Malicious Authdir Sanitized
# =====================================================================
def test_malicious_authdir_sanitized():
    # Path traversal attempts
    assert sanitize_authdir("../../etc/passwd") == "opennds_auth"
    assert sanitize_authdir("../../../bin/sh") == "opennds_auth"
    assert sanitize_authdir("opennds_auth/../secret") == "opennds_auth"

    # Invalid special characters
    assert sanitize_authdir("auth<script>") == "opennds_auth"
    assert sanitize_authdir("auth?param=1") == "opennds_auth"

    # None or empty
    assert sanitize_authdir(None) == "opennds_auth"
    assert sanitize_authdir("") == "opennds_auth"

    # Legitimate authdir
    assert sanitize_authdir("opennds_auth") == "opennds_auth"
    assert sanitize_authdir("custom_portal_dir") == "custom_portal_dir"


# =====================================================================
# Scenario 10: Unsafe Redirect URLs Rejected
# =====================================================================
def test_unsafe_redirect_urls_rejected():
    fallback = "https://www.google.com"

    # Javascript protocol handlers
    assert sanitize_redirect_url("javascript:alert(document.cookie)") == fallback
    assert sanitize_redirect_url("JAVASCRIPT:alert(1)") == fallback

    # Data and file schemes
    assert sanitize_redirect_url("data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==") == fallback
    assert sanitize_redirect_url("file:///etc/shadow") == fallback

    # CRLF injection
    assert sanitize_redirect_url("https://campus.edu.in/\r\nSet-Cookie: evil=1") == fallback
    assert sanitize_redirect_url("http://campus.edu.in/\nInjected-Header: true") == fallback

    # Missing netloc / invalid scheme
    assert sanitize_redirect_url("not_a_valid_url") == fallback
    assert sanitize_redirect_url("http://") == fallback

    # Legitimate URLs
    assert sanitize_redirect_url("https://www.google.com") == "https://www.google.com"
    assert sanitize_redirect_url("http://campus.edu.in/portal/dashboard") == "http://campus.edu.in/portal/dashboard"


# =====================================================================
# Scenario 11: Legitimate FAS URL Construction
# =====================================================================
def test_legitimate_fas_url_construction():
    tok = compute_fas_token("1234567890abcdef")
    assert len(tok) == 64  # SHA-256 hexdigest

    url = build_opennds_auth_url(
        gatewayaddress=f"{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}",
        tok=tok,
        redir_url="https://www.google.com",
        authdir="opennds_auth"
    )

    expected_prefix = f"http://{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}/opennds_auth/?"
    assert url.startswith(expected_prefix)
    assert f"tok={tok}" in url
    assert "redir=https%3A%2F%2Fwww.google.com" in url


# =====================================================================
# Scenario 12: Compatibility with Existing Features
# =====================================================================
def test_system_compatibility_with_existing_features():
    # 1. Student self-registration
    reg_payload = {
        "college_usn": "ENG23CS0112",
        "name": "Helen Keller",
        "email": "helen.keller@campus.edu.in",
        "department": "Computer Science Core",
        "password": "SecurePassword123!"
    }
    reg_res = client.post("/api/v1/gateway/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["approval_status"] == "PENDING_APPROVAL"

    # 2. Admin approval
    admin_token = create_admin_token("admin_test", "Test Admin", "SUPERADMIN")
    appr_res = client.post(
        "/api/v1/gateway/students/ENG23CS0112/approval",
        json={"approval_status": "APPROVED", "admin_notes": "Verified enrollment"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "APPROVED"

    # 3. Approved student login
    login_res = client.post(
        "/api/v1/gateway/login",
        json={
            "college_usn": "ENG23CS0112",
            "password": "SecurePassword123!",
            "client_mac": "02:00:00:00:01:12",
            "simulate_gateway": True
        }
    )
    assert login_res.status_code == 200
    assert login_res.json()["gateway_authorized"] is True

    # 4. Quota exhaustion rejection
    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0112").first()
    st.used_quota_mb = st.daily_quota_mb  # Exhaust full allowance
    db.commit()
    db.close()

    exhaust_res = client.post(
        "/api/v1/gateway/login",
        json={
            "college_usn": "ENG23CS0112",
            "password": "SecurePassword123!",
            "client_mac": "02:00:00:00:01:12",
            "simulate_gateway": True
        }
    )
    assert exhaust_res.status_code == 403
    assert "exhausted" in exhaust_res.json()["detail"].lower()


# =====================================================================
# Scenario 13: Counter Reset with Subsequent Traffic (100 -> 0 -> 20 -> 120 MiB)
# =====================================================================
def test_counter_reset_with_subsequent_traffic():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0113",
            student_id="CS-0113",
            name="Isaac Newton",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:13",
            client_ip="192.168.214.113",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Step 1: Client generates 100 MiB (30 MiB up, 70 MiB down)
    poll1_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:13": {
                "ip": "192.168.214.113",
                "upload_bytes": 30 * BYTES_PER_MIB,
                "download_bytes": 70 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll1_clients):
        res1 = client.get("/api/v1/gateway/sessions")
        assert res1.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0113").first()
    sess_db = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:13").first()
    assert st.used_quota_mb == 100.0, f"Expected 100.0 MiB, got {st.used_quota_mb}"
    assert sess_db.bytes_uploaded == 30 * BYTES_PER_MIB
    assert sess_db.bytes_downloaded == 70 * BYTES_PER_MIB
    db.close()

    # Step 2: Router counter resets to 0 (reboot or counter cycle)
    poll2_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:13": {
                "ip": "192.168.214.113",
                "upload_bytes": 0,
                "download_bytes": 0,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll2_clients):
        res2 = client.get("/api/v1/gateway/sessions")
        assert res2.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0113").first()
    sess_db = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:13").first()
    assert st.used_quota_mb == 100.0, "Used quota must not decrease on reset"
    assert "counter reset/decrease detected" in (sess_db.notes or "").lower()
    assert sess_db.traffic_completeness == "UNCERTAIN"
    db.close()

    # Step 3: Client generates 20 MiB post-reset (5 MiB up, 15 MiB down on router)
    poll3_clients = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:13": {
                "ip": "192.168.214.113",
                "upload_bytes": 5 * BYTES_PER_MIB,
                "download_bytes": 15 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll3_clients):
        res3 = client.get("/api/v1/gateway/sessions")
        assert res3.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0113").first()
    sess_db = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:13").first()
    assert st.used_quota_mb == 120.0, f"Usage must increase by post-reset 20 MiB to 120.0 MiB, got {st.used_quota_mb}"
    assert sess_db.bytes_uploaded == 35 * BYTES_PER_MIB
    assert sess_db.bytes_downloaded == 85 * BYTES_PER_MIB
    db.close()

    # Step 4: Repeated poll with traffic unchanged (stays 120.0 MiB)
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll3_clients):
        res4 = client.get("/api/v1/gateway/sessions")
        assert res4.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0113").first()
    assert st.used_quota_mb == 120.0, "Subsequent unchanged poll must not double count post-reset traffic"
    db.close()


# =====================================================================
# Scenario 14: Asymmetric Counter Reset
# =====================================================================
def test_asymmetric_counter_reset():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0114",
            student_id="CS-0114",
            name="Ada Lovelace",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:14",
            client_ip="192.168.214.114",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Step 1: Baseline 20 MiB up, 30 MiB down (50 MiB)
    poll1 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:14": {
                "ip": "192.168.214.114",
                "upload_bytes": 20 * BYTES_PER_MIB,
                "download_bytes": 30 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll1):
        res1 = client.get("/api/v1/gateway/sessions")
        assert res1.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0114").first()
    assert st.used_quota_mb == 50.0
    db.close()

    # Step 2: Upload resets to 0, while download normal increments from 30 -> 40 MiB
    poll2 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:14": {
                "ip": "192.168.214.114",
                "upload_bytes": 0,
                "download_bytes": 40 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll2):
        res2 = client.get("/api/v1/gateway/sessions")
        assert res2.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0114").first()
    sess_db = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:14").first()
    # Download delta is 10 MiB, upload delta is 0 -> total 60.0 MiB
    assert st.used_quota_mb == 60.0, f"Expected 60.0 MiB after asymmetric reset, got {st.used_quota_mb}"
    assert "upload: 20971520 -> 0" in sess_db.notes
    db.close()

    # Step 3: Upload produces 5 MiB post-reset, download stays at 40 MiB
    poll3 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:14": {
                "ip": "192.168.214.114",
                "upload_bytes": 5 * BYTES_PER_MIB,
                "download_bytes": 40 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll3):
        res3 = client.get("/api/v1/gateway/sessions")
        assert res3.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0114").first()
    assert st.used_quota_mb == 65.0, f"Expected 65.0 MiB, got {st.used_quota_mb}"
    db.close()


# =====================================================================
# Scenario 15: Ambiguous Counter Decrease Triggers Uncertainty
# =====================================================================
def test_ambiguous_counter_decrease_triggers_uncertainty():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0115",
            student_id="CS-0115",
            name="Alan Turing",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:15",
            client_ip="192.168.214.115",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Step 1: Initial reading of 100 MiB (30 up, 70 down)
    poll1 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:15": {
                "ip": "192.168.214.115",
                "upload_bytes": 30 * BYTES_PER_MIB,
                "download_bytes": 70 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll1):
        res1 = client.get("/api/v1/gateway/sessions")
        assert res1.status_code == 200

    # Step 2: Ambiguous decrease to 25 up, 55 down (total 80 MiB, drop of 20 MiB)
    poll2 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:15": {
                "ip": "192.168.214.115",
                "upload_bytes": 25 * BYTES_PER_MIB,
                "download_bytes": 55 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll2):
        res2 = client.get("/api/v1/gateway/sessions")
        assert res2.status_code == 200

    db = TestSessionLocal()
    sess_db = db.query(GatewaySession).filter(GatewaySession.client_mac == "02:00:00:00:01:15").first()
    assert "counter reset/decrease detected" in sess_db.notes.lower()
    assert sess_db.traffic_completeness == "UNCERTAIN"
    db.close()


# =====================================================================
# Scenario 16: Actual Usage Exceeding Quota Unclamped and Enforced
# =====================================================================
def test_actual_usage_exceeding_quota_unclamped_and_enforced():
    db = TestSessionLocal()
    try:
        student = Student(
            college_usn="ENG23CS0116",
            student_id="CS-0116",
            name="Margaret Hamilton",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1000.0,
            used_quota_mb=0.0,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:16",
            client_ip="192.168.214.116",
            session_start=datetime.utcnow(),
            quota_assigned_kb=1000.0 * 1024,
            bytes_uploaded=0.0,
            bytes_downloaded=0.0,
            status="ACTIVE"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Router reports 1050 MiB transferred (overshooting 1000 MiB quota)
    poll_overshoot = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:16": {
                "ip": "192.168.214.116",
                "upload_bytes": 350 * BYTES_PER_MIB,
                "download_bytes": 700 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll_overshoot):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0116").first()
    # 1. Actual usage must NOT be clamped to 1000.0
    assert st.used_quota_mb == 1050.0, f"Actual measured usage must be preserved, got {st.used_quota_mb}"

    # 2. Remaining quota must be 0.0 (never negative)
    from app.routers.gateway import _calculate_remaining_quota
    assert _calculate_remaining_quota(st) == 0.0

    # 3. Subsequent login attempt must be rejected with HTTP 403 Quota Exhausted
    login_res = client.post(
        "/api/v1/gateway/login",
        json={
            "college_usn": "ENG23CS0116",
            "password": "Password123!",
            "client_mac": "02:00:00:00:01:16",
            "simulate_gateway": True
        }
    )
    assert login_res.status_code == 403
    assert "exhausted" in login_res.json()["detail"].lower()
    db.close()


# =====================================================================
# Scenario 17: Daily Rollover Mid-Session Across Midnight Boundary
# =====================================================================
def test_daily_rollover_mid_session_boundary():
    db = TestSessionLocal()
    yesterday = date.today() - timedelta(days=1)
    try:
        student = Student(
            college_usn="ENG23CS0117",
            student_id="CS-0117",
            name="John von Neumann",
            department="Computer Science",
            academic_year="3rd Year",
            approval_status="APPROVED",
            password_hash=hash_password("Password123!"),
            daily_quota_mb=1024.0,
            used_quota_mb=100.0,  # 100 MiB used yesterday
            quota_reset_date=yesterday,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Active session from yesterday with baseline tag of 100 MiB (30 up, 70 down)
        sess = GatewaySession(
            student_id=student.id,
            client_mac="02:00:00:00:01:17",
            client_ip="192.168.214.117",
            session_start=datetime.utcnow() - timedelta(hours=6),
            quota_assigned_kb=1024.0 * 1024,
            bytes_uploaded=30.0 * BYTES_PER_MIB,
            bytes_downloaded=70.0 * BYTES_PER_MIB,
            status="ACTIVE",
            notes=f"[router_baseline: up={30 * BYTES_PER_MIB:.0f}, down={70 * BYTES_PER_MIB:.0f}]"
        )
        db.add(sess)
        db.commit()
    finally:
        db.close()

    # Client now reports 120 MiB on router (35 MiB up, 85 MiB down -> 20 MiB transferred on Day 2)
    poll_day2 = {
        "client_list_length": 1,
        "clients": {
            "02:00:00:00:01:17": {
                "ip": "192.168.214.117",
                "upload_bytes": 35 * BYTES_PER_MIB,
                "download_bytes": 85 * BYTES_PER_MIB,
                "state": "authenticated"
            }
        }
    }
    with patch("app.routers.gateway.gateway_service.get_live_clients", return_value=poll_day2):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200

    db = TestSessionLocal()
    st = db.query(Student).filter(Student.college_usn == "ENG23CS0117").first()
    # Rollover should reset yesterday's 100 MiB and charge ONLY today's 20 MiB
    assert st.quota_reset_date == date.today()
    assert st.used_quota_mb == 20.0, f"Expected only 20.0 MiB charged for Day 2, got {st.used_quota_mb}"
    db.close()


# =====================================================================
# Scenario 18: Traffic Completeness Evaluation Semantics
# =====================================================================
def test_traffic_completeness_semantics():
    # 1. Active session without anomalies -> IN_PROGRESS
    s_active = GatewaySession(status="ACTIVE", notes=None)
    assert s_active.traffic_completeness == "IN_PROGRESS"

    # 2. Session with counter reset/decrease -> UNCERTAIN
    s_reset = GatewaySession(status="ACTIVE", notes="[Accounting Uncertainty: Counter reset/decrease detected]")
    assert s_reset.traffic_completeness == "UNCERTAIN"

    # 3. Closed session with counter decrease -> UNCERTAIN
    s_closed_reset = GatewaySession(status="EXPIRED", notes="anomaly occurred during poll")
    assert s_closed_reset.traffic_completeness == "UNCERTAIN"

    # 4. Closed session with affirmative verification marker -> COMPLETE
    s_complete = GatewaySession(status="EXPIRED", notes="Session concluded successfully [FINAL_COUNTER_VERIFIED]")
    assert s_complete.traffic_completeness == "COMPLETE"

    # 5. Closed session without verification marker -> LAST_KNOWN_INCOMPLETE
    s_incomplete_expired = GatewaySession(status="EXPIRED", notes="Client disconnected")
    assert s_incomplete_expired.traffic_completeness == "LAST_KNOWN_INCOMPLETE"

    s_incomplete_deauth = GatewaySession(status="DEAUTHED", notes="Admin deauth")
    assert s_incomplete_deauth.traffic_completeness == "LAST_KNOWN_INCOMPLETE"

    s_incomplete_super = GatewaySession(status="SUPERSEDED", notes="MAC reassigned")
    assert s_incomplete_super.traffic_completeness == "LAST_KNOWN_INCOMPLETE"

    # 6. Legacy session with None notes -> LAST_KNOWN_INCOMPLETE
    s_legacy = GatewaySession(status="EXPIRED", notes=None)
    assert s_legacy.traffic_completeness == "LAST_KNOWN_INCOMPLETE"


# =====================================================================
# Scenario 19: Captive-Portal Redirect Security Hardening
# =====================================================================
def test_redirect_security_hardening():
    fallback = "https://www.google.com"

    # 1. Embedded credentials (@, username, password) rejected
    assert sanitize_redirect_url("http://user:pass@evil.com/login") == fallback
    assert sanitize_redirect_url("http://admin@trusted.com/portal") == fallback

    # 2. Backslashes rejected (host confusion)
    assert sanitize_redirect_url("http://trusted.com\\evil.com") == fallback
    assert sanitize_redirect_url("https://campus.edu.in\\path\\sub") == fallback

    # 3. Control characters and CRLF rejected
    assert sanitize_redirect_url("http://campus.edu.in/\x00test") == fallback
    assert sanitize_redirect_url("http://campus.edu.in/\x1b[31mred") == fallback
    assert sanitize_redirect_url("http://campus.edu.in/\r\nSet-Cookie: token=123") == fallback

    # 4. Valid HTTP/HTTPS accepted
    assert sanitize_redirect_url("https://www.google.com/search?q=openwrt") == "https://www.google.com/search?q=openwrt"
    assert sanitize_redirect_url("http://campus.edu.in:8080/portal") == "http://campus.edu.in:8080/portal"

    # 5. Token tok is strictly gateway parameter and never passed into redir target
    tok = compute_fas_token("test_origin_token")
    auth_url = build_opennds_auth_url(
        gatewayaddress="192.168.214.1:2050",
        tok=tok,
        redir_url="https://www.google.com"
    )
    # The gateway auth URL contains ?tok=...
    assert f"tok={tok}" in auth_url
    # The redir parameter inside the auth URL does not contain any nested token
    assert "redir=https%3A%2F%2Fwww.google.com" in auth_url
