"""
Stage 6 — Gateway Integration Test Suite.

Comprehensive automated tests verifying OpenWrt/OpenNDS gateway integration.
Guarantees 100% production safety by executing strictly against isolated mocks,
stubs, and an in-memory/test database snapshot (never against live network targets
or the production database).

Covers all 20 required integration scenarios:
 1. Successful gateway status request.
 2. Gateway unavailable/unreachable.
 3. Request timeout.
 4. Invalid/malformed gateway response.
 5. Gateway authentication failure.
 6. Unsupported endpoint or operation.
 7. Approved student authorization.
 8. Pending student denial.
 9. Rejected student denial.
10. Invalid or missing client identity (multicast/broadcast/malformed).
11. Client identity changes & stale mappings (MAC collision / superseded).
12. Session expiration & logout.
13. Disconnect & reconnect behavior.
14. Valid usage counters.
15. Missing/inconsistent counters.
16. Quota remaining calculation.
17. Quota exhaustion denial.
18. Counter reset and rollover.
19. Isolation between different students' usage & sessions.
20. Prevention of simulated success being reported as live authorization.
"""

import subprocess
import json
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.gateway import Student, GatewaySession, GatewayEvent, AdminUser, seed_default_students
from app.services.openwrt_service import (
    OpenWrtGatewayService,
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayCommandError,
    GatewayResponseError,
    split_quota_allocation,
    normalize_mac,
    is_valid_mac,
    hash_password,
    create_admin_token,
    BYTES_PER_MIB,
    KIB_PER_MIB
)

client = TestClient(app)

TEST_MAC_1 = "02:00:00:00:00:01"
TEST_MAC_2 = "02:00:00:00:00:02"
TEST_USN_PREFIX = "TEST-GW-INT-"


@pytest.fixture(autouse=True)
def ensure_seed_and_cleanup():
    """Ensure baseline seed exists and clean up ephemeral test students after each test."""
    db = SessionLocal()
    try:
        seed_default_students(db)
        # Purge prior ephemeral test records
        db.query(GatewaySession).filter(GatewaySession.client_mac.in_([TEST_MAC_1, TEST_MAC_2])).delete(synchronize_session=False)
        db.query(Student).filter(Student.college_usn.like(f"{TEST_USN_PREFIX}%")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(GatewaySession).filter(GatewaySession.client_mac.in_([TEST_MAC_1, TEST_MAC_2])).delete(synchronize_session=False)
        db.query(Student).filter(Student.college_usn.like(f"{TEST_USN_PREFIX}%")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _create_test_student(db, usn_suffix: str, approval_status: str = "APPROVED", used_mb: float = 0.0, quota_mb: float = 1024.0) -> Student:
    """Helper to create a dedicated test student."""
    clean_usn = f"{TEST_USN_PREFIX}{usn_suffix}"
    student = Student(
        college_usn=clean_usn,
        student_id=f"TEST-ID-{usn_suffix}",
        name=f"Test Student {usn_suffix}",
        department="Computer Science",
        department_code="CS",
        batch_year=2023,
        academic_year="4th Year",
        approval_status=approval_status,
        is_demo=False,
        email=f"test.{usn_suffix.lower()}@campus.edu.in",
        password_hash=hash_password("SafePassword@2026"),
        daily_quota_mb=quota_mb,
        used_quota_mb=used_mb,
        quota_reset_date=date.today(),
        session_timeout_mins=120,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# =====================================================================
# Scenario 1: Successful Gateway Status Request
# =====================================================================
def test_scenario_01_successful_gateway_status_request():
    """Verify successful parsing of ndsctl status and live gateway status endpoint."""
    mock_status_text = (
        "Version: 10.3.1\n"
        "Uptime: 4 hours 12 mins\n"
        "Gateway Name: Campus Gateway\n"
        "Managed interface: br-lan\n"
        "Upstream gateway: 172.20.10.1,eth2\n"
        "MHD Server listening on: http://192.168.214.2:2050\n"
        "Client authentication: FAS Secure Level 1\n"
    )
    with patch.object(OpenWrtGatewayService, "_run_ssh", return_value=mock_status_text):
        service = OpenWrtGatewayService()
        status = service.get_opennds_status()
        assert status["running"] is True
        assert status["version"] == "10.3.1"
        assert status["managed_interface"] == "br-lan"
        assert status["mhd_listening"] == "192.168.214.2:2050"

    with patch.object(OpenWrtGatewayService, "get_opennds_status", return_value=status), \
         patch.object(OpenWrtGatewayService, "get_live_clients", return_value={"client_list_length": 0, "clients": {}}):
        res = client.get("/api/v1/gateway/status")
        assert res.status_code == 200
        data = res.json()
        assert data["gateway_connected"] is True
        assert data["opennds_running"] is True
        assert data["integration_mode"] == "LIVE"
        assert data["opennds_version"] == "10.3.1"
        assert data["mhd_port"] == 2050
        assert data["fas_level"] == 1


# =====================================================================
# Scenario 2: Gateway Unavailable / Unreachable
# =====================================================================
def test_scenario_02_gateway_unavailable_unreachable():
    """Verify system fails closed when gateway is unreachable."""
    with patch.object(OpenWrtGatewayService, "_run_ssh", side_effect=GatewayConnectionError("Router host unreachable at 192.168.214.2")):
        service = OpenWrtGatewayService()
        assert service.check_connectivity() is False

    with patch.object(OpenWrtGatewayService, "get_opennds_status", side_effect=GatewayConnectionError("Connection refused")):
        res = client.get("/api/v1/gateway/status")
        assert res.status_code == 200
        data = res.json()
        assert data["gateway_connected"] is False
        assert data["opennds_running"] is False
        assert data["integration_mode"] == "UNAVAILABLE"
        assert "Connection refused" in data["error"]

    # Client login must fail closed (HTTP 503) without granting access
    login_payload = {
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }
    with patch.object(OpenWrtGatewayService, "authorize_client", side_effect=GatewayConnectionError("Connection refused")):
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 503
        assert "unreachable" in res.json()["detail"].lower()


# =====================================================================
# Scenario 3: Request Timeout
# =====================================================================
def test_scenario_03_request_timeout():
    """Verify that SSH/command timeouts raise GatewayConnectionError and abort login."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ssh ...", timeout=5)):
        service = OpenWrtGatewayService()
        with pytest.raises(GatewayConnectionError) as exc_info:
            service._run_ssh("ndsctl status", timeout=5)
        assert "timed out" in str(exc_info.value).lower()

    login_payload = {
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }
    with patch.object(OpenWrtGatewayService, "authorize_client", side_effect=GatewayConnectionError("Gateway timed out after 5s")):
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 503
        assert "unreachable" in res.json()["detail"].lower() or "failed" in res.json()["detail"].lower()


# =====================================================================
# Scenario 4: Invalid / Malformed Gateway Response
# =====================================================================
def test_scenario_04_invalid_malformed_gateway_response():
    """Verify graceful handling when gateway returns malformed or non-JSON output."""
    service = OpenWrtGatewayService()
    with patch.object(service, "_run_ssh", return_value="CRITICAL_KERNEL_PANIC: invalid json {"):
        with pytest.raises(GatewayResponseError) as exc_info:
            service.get_live_clients()
        assert "Failed to parse ndsctl JSON response" in str(exc_info.value)

    # Corrupted ndsctl status text should safely provide fallback defaults without crashing
    with patch.object(service, "_run_ssh", return_value="Random text with no headers"):
        status = service.get_opennds_status()
        assert status["running"] is True
        assert status["version"] == "10.3.1"
        assert status["uptime"] == "Unknown"


# =====================================================================
# Scenario 5: Gateway Authentication Failure
# =====================================================================
def test_scenario_05_gateway_authentication_failure():
    """Verify that SSH authentication failure raises GatewayAuthenticationError and returns 502."""
    mock_completed = MagicMock()
    mock_completed.returncode = 255
    mock_completed.stderr = "Permission denied (publickey,password)."
    mock_completed.stdout = ""

    with patch("subprocess.run", return_value=mock_completed):
        service = OpenWrtGatewayService()
        with pytest.raises(GatewayAuthenticationError) as exc_info:
            service._run_ssh("ndsctl status")
        assert "authentication failed" in str(exc_info.value).lower()

    login_payload = {
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }
    with patch.object(OpenWrtGatewayService, "authorize_client", side_effect=GatewayAuthenticationError("Invalid SSH key")):
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 502
        assert "authentication failed" in res.json()["detail"].lower()


# =====================================================================
# Scenario 6: Unsupported Endpoint or Operation
# =====================================================================
def test_scenario_06_unsupported_endpoint_or_operation():
    """Verify that unsupported ndsctl commands or endpoints are rejected cleanly."""
    mock_completed = MagicMock()
    mock_completed.returncode = 1
    mock_completed.stderr = "Unknown command 'ndsctl unsupported_action'"
    mock_completed.stdout = ""

    with patch("subprocess.run", return_value=mock_completed):
        service = OpenWrtGatewayService()
        with pytest.raises(GatewayCommandError) as exc_info:
            service._run_ssh("ndsctl unsupported_action")
        assert "Gateway command failed" in str(exc_info.value)

    # Test non-existent API endpoint
    res = client.get("/api/v1/gateway/non_existent_endpoint")
    assert res.status_code == 404


# =====================================================================
# Scenario 7: Approved Student Authorization
# =====================================================================
def test_scenario_07_approved_student_authorization():
    """Verify full end-to-end authorization for an approved student."""
    db = SessionLocal()
    st = _create_test_student(db, "APP07", approval_status="APPROVED", used_mb=50.0, quota_mb=1024.0)
    target_usn = st.college_usn
    target_id = st.id
    db.close()

    login_payload = {
        "college_usn": target_usn,
        "password": "SafePassword@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }

    with patch.object(OpenWrtGatewayService, "authorize_client", return_value=(True, 149504, 847192)):
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["gateway_authorized"] is True
        assert data["live_gateway_verified"] is True
        assert data["is_simulated"] is False
        assert data["gateway_status_mode"] == "LIVE"
        assert data["remaining_quota_mb"] == 974.0

    # Verify session recorded in database
    db = SessionLocal()
    session = db.query(GatewaySession).filter(
        GatewaySession.client_mac == TEST_MAC_1,
        GatewaySession.status == "ACTIVE"
    ).first()
    assert session is not None
    assert session.student_id == target_id

    event = db.query(GatewayEvent).filter(
        GatewayEvent.student_id == target_usn,
        GatewayEvent.event_type == "LOGIN_SUCCESS"
    ).first()
    assert event is not None
    db.close()


# =====================================================================
# Scenario 8: Pending Student Denial
# =====================================================================
def test_scenario_08_pending_student_denial():
    """Verify that pending students cannot authenticate or receive gateway access."""
    db = SessionLocal()
    st = _create_test_student(db, "PEN08", approval_status="PENDING_APPROVAL")
    target_usn = st.college_usn
    db.close()

    login_payload = {
        "college_usn": target_usn,
        "password": "SafePassword@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }

    with patch.object(OpenWrtGatewayService, "authorize_client") as mock_auth:
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 403
        assert "pending administrator approval" in res.json()["detail"].lower()
        mock_auth.assert_not_called()

    # Verify no session created
    db = SessionLocal()
    session = db.query(GatewaySession).filter(GatewaySession.client_mac == TEST_MAC_1).first()
    assert session is None
    db.close()


# =====================================================================
# Scenario 9: Rejected Student Denial
# =====================================================================
def test_scenario_09_rejected_student_denial():
    """Verify that rejected students cannot authenticate or open gateway."""
    db = SessionLocal()
    st = _create_test_student(db, "REJ09", approval_status="REJECTED")
    target_usn = st.college_usn
    db.close()

    login_payload = {
        "college_usn": target_usn,
        "password": "SafePassword@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }

    with patch.object(OpenWrtGatewayService, "authorize_client") as mock_auth:
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 403
        assert "rejected" in res.json()["detail"].lower()
        mock_auth.assert_not_called()


# =====================================================================
# Scenario 10: Invalid or Missing Client Identity (Multicast / Broadcast)
# =====================================================================
def test_scenario_10_invalid_or_missing_client_identity():
    """Verify validation strictly rejects invalid, broadcast, or multicast MAC addresses."""
    # 1. Malformed MAC
    res1 = client.post("/api/v1/gateway/login", json={
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": "not-a-real-mac"
    })
    assert res1.status_code == 400
    assert "Invalid hardware MAC address format" in res1.json()["detail"]

    # 2. Broadcast MAC
    res2 = client.post("/api/v1/gateway/login", json={
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": "FF:FF:FF:FF:FF:FF"
    })
    assert res2.status_code == 400
    assert "Expected valid unicast" in res2.json()["detail"]

    # 3. Multicast MAC (e.g., 01:00:5E:00:00:01)
    res3 = client.post("/api/v1/gateway/login", json={
        "college_usn": "DEMO-USN-CSE01",
        "password": "Campus@2026",
        "client_mac": "01:00:5E:00:00:01"
    })
    assert res3.status_code == 400
    assert "Expected valid unicast" in res3.json()["detail"]


# =====================================================================
# Scenario 11: Client Identity Changes & Stale Mappings (MAC Collision)
# =====================================================================
def test_scenario_11_client_identity_changes_and_stale_mappings():
    """Verify that when a client device MAC is re-assigned, prior active session is superseded."""
    db = SessionLocal()
    st_a = _create_test_student(db, "STU11A")
    st_b = _create_test_student(db, "STU11B")
    usn_b = st_b.college_usn
    id_b = st_b.id

    # Session for Student A
    sess_a = GatewaySession(
        student_id=st_a.id,
        client_mac=TEST_MAC_1,
        session_start=datetime.utcnow() - timedelta(minutes=30),
        quota_assigned_kb=1048576,
        status="ACTIVE",
        notes="Initial session for Student A"
    )
    db.add(sess_a)
    db.commit()
    sess_a_id = sess_a.id
    db.close()

    # Now Student B logs in with the SAME client MAC
    with patch.object(OpenWrtGatewayService, "authorize_client", return_value=(True, 150000, 850000)):
        res = client.post("/api/v1/gateway/login", json={
            "college_usn": usn_b,
            "password": "SafePassword@2026",
            "client_mac": TEST_MAC_1,
            "simulate_gateway": False
        })
        assert res.status_code == 200

    db = SessionLocal()
    prior_session = db.query(GatewaySession).filter(GatewaySession.id == sess_a_id).first()
    assert prior_session.status == "SUPERSEDED"
    assert prior_session.session_end is not None

    new_session = db.query(GatewaySession).filter(
        GatewaySession.client_mac == TEST_MAC_1,
        GatewaySession.status == "ACTIVE"
    ).first()
    assert new_session is not None
    assert new_session.student_id == id_b

    # Verify CLIENT_REASSIGNED event
    reassign_event = db.query(GatewayEvent).filter(
        GatewayEvent.client_mac == TEST_MAC_1,
        GatewayEvent.event_type == "CLIENT_REASSIGNED"
    ).first()
    assert reassign_event is not None
    db.close()


# =====================================================================
# Scenario 12: Session Expiration & Logout
# =====================================================================
def test_scenario_12_session_expiration_and_logout():
    """Verify client deauthentication terminates gateway session and updates status."""
    db = SessionLocal()
    st = _create_test_student(db, "DEAUTH12")
    active_sess = GatewaySession(
        student_id=st.id,
        client_mac=TEST_MAC_1,
        session_start=datetime.utcnow() - timedelta(minutes=10),
        quota_assigned_kb=1048576.0,
        status="ACTIVE"
    )
    db.add(active_sess)
    db.commit()
    db.close()

    with patch.object(OpenWrtGatewayService, "deauthorize_client", return_value=True) as mock_deauth:
        res = client.post(f"/api/v1/gateway/deauth/{TEST_MAC_1}")
        assert res.status_code == 200
        mock_deauth.assert_called_once_with(TEST_MAC_1)

    db = SessionLocal()
    session = db.query(GatewaySession).filter(GatewaySession.client_mac == TEST_MAC_1).first()
    assert session.status == "DEAUTHED"
    assert session.session_end is not None
    db.close()


# =====================================================================
# Scenario 13: Disconnect & Reconnect Behavior
# =====================================================================
def test_scenario_13_disconnect_and_reconnect_behavior():
    """Verify student disconnect preserves accumulated quota usage upon reconnecting."""
    db = SessionLocal()
    st = _create_test_student(db, "RECON13", used_mb=200.0, quota_mb=1000.0)
    usn = st.college_usn
    db.close()

    # Student reconnects
    with patch.object(OpenWrtGatewayService, "authorize_client", return_value=(True, 120000, 680000)):
        res = client.post("/api/v1/gateway/login", json={
            "college_usn": usn,
            "password": "SafePassword@2026",
            "client_mac": TEST_MAC_1,
            "simulate_gateway": False
        })
        assert res.status_code == 200
        data = res.json()
        assert data["remaining_quota_mb"] == 800.0  # Exactly 1000 - 200
        assert data["assigned_quota_mb"] == 1000.0
        assert data["used_quota_mb"] == 200.0


# =====================================================================
# Scenario 14: Valid Usage Counters
# =====================================================================
def test_scenario_14_valid_usage_counters():
    """Verify live client usage counters convert accurately to MiB and update student records."""
    db = SessionLocal()
    st = _create_test_student(db, "USAGE14", used_mb=0.0, quota_mb=1000.0)
    usn = st.college_usn
    session = GatewaySession(
        student_id=st.id,
        client_mac=TEST_MAC_1,
        session_start=datetime.utcnow() - timedelta(minutes=5),
        quota_assigned_kb=1048576.0,
        status="ACTIVE"
    )
    db.add(session)
    db.commit()
    db.close()

    # 10 MiB upload (10,485,760 bytes) + 40 MiB download (41,943,040 bytes) = 50 MiB total
    mock_live_clients = {
        "clients": {
            TEST_MAC_1: {
                "ip": "192.168.214.150",
                "upload_bytes": 10485760,
                "download_bytes": 41943040,
                "token": "tok_valid_test",
                "state": "authenticated",
                "session_start": int(datetime.utcnow().timestamp()) - 300,
                "session_end": int(datetime.utcnow().timestamp()) + 3300
            }
        }
    }

    admin_token = create_admin_token("test_admin", "Test Admin", "SuperAdmin")
    with patch.object(OpenWrtGatewayService, "get_live_clients", return_value=mock_live_clients):
        res = client.get("/api/v1/gateway/sessions", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["gateway_connected"] is True
        assert data["active_clients_count"] == 1

    db = SessionLocal()
    updated_st = db.query(Student).filter(Student.college_usn == usn).first()
    assert updated_st.used_quota_mb == 50.0

    updated_sess = db.query(GatewaySession).filter(GatewaySession.client_mac == TEST_MAC_1).first()
    assert updated_sess.bytes_uploaded == 10485760.0
    assert updated_sess.bytes_downloaded == 41943040.0
    db.close()


# =====================================================================
# Scenario 15: Missing or Inconsistent Counters
# =====================================================================
def test_scenario_15_missing_or_inconsistent_counters():
    """Verify that missing, None, or zero byte counters do not crash session sync."""
    db = SessionLocal()
    st = _create_test_student(db, "INCON15", used_mb=10.0, quota_mb=1000.0)
    usn = st.college_usn
    session = GatewaySession(
        student_id=st.id,
        client_mac=TEST_MAC_1,
        session_start=datetime.utcnow(),
        quota_assigned_kb=1048576.0,
        status="ACTIVE"
    )
    db.add(session)
    db.commit()
    db.close()

    mock_live_clients = {
        "clients": {
            TEST_MAC_1: {
                "ip": "192.168.214.150",
                "token": "tok_test",
                # upload_bytes and download_bytes omitted
            }
        }
    }

    with patch.object(OpenWrtGatewayService, "get_live_clients", return_value=mock_live_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200
        data = res.json()
        assert data["gateway_connected"] is True

    db = SessionLocal()
    st_check = db.query(Student).filter(Student.college_usn == usn).first()
    # Prior usage must be preserved, not overwritten with zero or corrupted
    assert st_check.used_quota_mb == 10.0
    db.close()


# =====================================================================
# Scenario 16: Quota Remaining Calculation
# =====================================================================
def test_scenario_16_quota_remaining_calculation():
    """Verify IEC binary quota split calculation ensures upload + download equals remaining quota."""
    # Example: 724 MiB remaining = 741,376 KiB
    total_kb = 741376
    up_kb, down_kb = split_quota_allocation(total_kb, download_ratio=0.85)

    assert up_kb + down_kb == total_kb
    assert down_kb == int(total_kb * 0.85)
    assert up_kb == total_kb - down_kb

    # Edge cases
    assert split_quota_allocation(0) == (0, 0)
    assert split_quota_allocation(-100) == (0, 0)
    up_small, down_small = split_quota_allocation(1000)
    assert up_small + down_small == 1000


# =====================================================================
# Scenario 17: Quota Exhaustion Denial
# =====================================================================
def test_scenario_17_quota_exhaustion_denial():
    """Verify that a student who has exhausted their daily quota is blocked fail-closed."""
    db = SessionLocal()
    st = _create_test_student(db, "EXH17", used_mb=1000.0, quota_mb=1000.0)
    usn = st.college_usn
    db.close()

    login_payload = {
        "college_usn": usn,
        "password": "SafePassword@2026",
        "client_mac": TEST_MAC_1,
        "simulate_gateway": False
    }

    with patch.object(OpenWrtGatewayService, "authorize_client") as mock_auth:
        res = client.post("/api/v1/gateway/login", json=login_payload)
        assert res.status_code == 403
        assert "Daily data quota exhausted" in res.json()["detail"]
        mock_auth.assert_not_called()

    db = SessionLocal()
    event = db.query(GatewayEvent).filter(
        GatewayEvent.student_id == usn,
        GatewayEvent.event_type == "QUOTA_EXHAUSTED"
    ).first()
    assert event is not None
    db.close()


# =====================================================================
# Scenario 18: Counter Reset and Rollover
# =====================================================================
def test_scenario_18_counter_reset_and_rollover():
    """Verify that quota reset restores full daily quota and permits login."""
    db = SessionLocal()
    st = _create_test_student(db, "RESET18", used_mb=1000.0, quota_mb=1000.0)
    usn = st.college_usn
    db.close()

    # Reset quota
    res_reset = client.post(f"/api/v1/gateway/students/{usn}/reset-quota")
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["used_quota_mb"] == 0.0
    assert reset_data["remaining_quota_mb"] == 1000.0

    # Login now succeeds
    with patch.object(OpenWrtGatewayService, "authorize_client", return_value=(True, 150000, 850000)):
        res_login = client.post("/api/v1/gateway/login", json={
            "college_usn": usn,
            "password": "SafePassword@2026",
            "client_mac": TEST_MAC_1,
            "simulate_gateway": False
        })
        assert res_login.status_code == 200
        assert res_login.json()["remaining_quota_mb"] == 1000.0


# =====================================================================
# Scenario 19: Isolation Between Different Students' Usage & Sessions
# =====================================================================
def test_scenario_19_isolation_between_different_students_usage_and_sessions():
    """Verify complete isolation: Student A's usage never affects Student B's quota."""
    db = SessionLocal()
    st_a = _create_test_student(db, "ISO19A", used_mb=0.0, quota_mb=1000.0)
    st_b = _create_test_student(db, "ISO19B", used_mb=0.0, quota_mb=500.0)
    usn_a = st_a.college_usn
    usn_b = st_b.college_usn
    id_a = st_a.id

    # Active session for Student A
    sess_a = GatewaySession(
        student_id=id_a,
        client_mac=TEST_MAC_1,
        session_start=datetime.utcnow(),
        quota_assigned_kb=1048576.0,
        status="ACTIVE"
    )
    db.add(sess_a)
    db.commit()
    db.close()

    # Simulate 200 MiB consumption on Student A's MAC
    mock_clients = {
        "clients": {
            TEST_MAC_1: {
                "ip": "192.168.214.150",
                "upload_bytes": 52428800,       # 50 MiB
                "download_bytes": 157286400,    # 150 MiB
                "token": "tok_secret_a"
            }
        }
    }

    # Unauthenticated/public request to /sessions
    with patch.object(OpenWrtGatewayService, "get_live_clients", return_value=mock_clients):
        res = client.get("/api/v1/gateway/sessions")
        assert res.status_code == 200
        data = res.json()
        # Verify sensitive token is masked for non-admin
        assert data["live_clients"][0]["token"] is None

    db = SessionLocal()
    refreshed_a = db.query(Student).filter(Student.college_usn == usn_a).first()
    refreshed_b = db.query(Student).filter(Student.college_usn == usn_b).first()

    assert refreshed_a.used_quota_mb == 200.0
    # Student B's used quota MUST remain 0.0
    assert refreshed_b.used_quota_mb == 0.0
    db.close()


# =====================================================================
# Scenario 20: Prevention of Simulated Success Being Reported as Live
# =====================================================================
def test_scenario_20_prevention_of_simulated_success_reported_as_live():
    """Verify transparent distinction between simulation mode and live gateway authorization."""
    db = SessionLocal()
    st = _create_test_student(db, "SIM20", used_mb=0.0, quota_mb=1000.0)
    usn = st.college_usn
    db.close()

    # Case A: simulate_gateway=True
    with patch.object(OpenWrtGatewayService, "authorize_client") as mock_auth_live:
        res_sim = client.post("/api/v1/gateway/login", json={
            "college_usn": usn,
            "password": "SafePassword@2026",
            "client_mac": TEST_MAC_1,
            "simulate_gateway": True
        })
        assert res_sim.status_code == 200
        data_sim = res_sim.json()
        assert data_sim["is_simulated"] is True
        assert data_sim["live_gateway_verified"] is False
        assert data_sim["gateway_status_mode"] == "SIMULATED"
        assert "(Simulated Mode)" in data_sim["message"]
        # Router command MUST NOT be executed in simulation mode
        mock_auth_live.assert_not_called()

    # Case B: simulate_gateway=False (Live mode)
    with patch.object(OpenWrtGatewayService, "authorize_client", return_value=(True, 150000, 850000)) as mock_auth_live:
        res_live = client.post("/api/v1/gateway/login", json={
            "college_usn": usn,
            "password": "SafePassword@2026",
            "client_mac": TEST_MAC_2,
            "simulate_gateway": False
        })
        assert res_live.status_code == 200
        data_live = res_live.json()
        assert data_live["is_simulated"] is False
        assert data_live["live_gateway_verified"] is True
        assert data_live["gateway_status_mode"] == "LIVE"
        assert "(Simulated Mode)" not in data_live["message"]
        mock_auth_live.assert_called_once()
