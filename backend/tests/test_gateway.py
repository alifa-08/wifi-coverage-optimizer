import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
import base64
import hashlib
from app.services.openwrt_service import (
    hash_password,
    verify_password,
    normalize_mac,
    is_valid_mac,
    split_quota_allocation,
    parse_fas_parameter,
    compute_fas_token,
    build_opennds_auth_url,
    DEFAULT_FAS_KEY,
    OpenWrtGatewayService,
    GatewayConnectionError,
    create_admin_token
)
from app.models.gateway import Student, GatewaySession, AdminUser, GatewayEvent, seed_default_students
from app.database import SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_gateway_db():
    db = SessionLocal()
    try:
        seed_default_students(db)
    finally:
        db.close()
    yield



def test_password_hashing():
    raw_pass = "SecurePass@2026"
    hashed = hash_password(raw_pass)
    assert ":" in hashed
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False
    assert verify_password("", hashed) is False


def test_mac_normalization_and_validation():
    assert is_valid_mac("00:50:56:c0:00:01") is True
    assert is_valid_mac("00-50-56-C0-00-01") is True
    assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    assert is_valid_mac("00:50:56:c0:00") is False
    assert is_valid_mac("invalid_mac") is False
    assert is_valid_mac("") is False

    assert normalize_mac("00-50-56-C0-00-01") == "00:50:56:c0:00:01"
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_quota_split_calculation():
    # Test binary IEC: 1,048,576 KiB (1 GiB)
    total_kb = 1048576
    up_kb, down_kb = split_quota_allocation(total_kb, download_ratio=0.85)
    # Strictly ensures sum equals total remaining budget
    assert up_kb + down_kb == total_kb
    assert down_kb > up_kb
    assert down_kb == int(total_kb * 0.85)


def test_ndsctl_command_construction():
    service = OpenWrtGatewayService()
    cmd = service.build_auth_command(
        target="00:50:56:c0:00:01",
        session_timeout_mins=120,
        upload_quota_kb=157286,
        download_quota_kb=891290,
        custom_identifier="Student:DEMO-USN-CSE01"
    )
    assert 'ndsctl auth "00:50:56:c0:00:01" 120 0 0 157286 891290 "Student:DEMO-USN-CSE01"' in cmd


def test_portal_landing_endpoint():
    res = client.get("/api/v1/gateway/portal?clientmac=00:50:56:c0:00:01&clientip=192.168.214.100&tok=tok123")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "portal_ready"
    assert data["client_mac"] == "00:50:56:c0:00:01"
    assert data["client_ip"] == "192.168.214.100"
    assert data["token"] == "tok123"


def test_list_students_and_quota_calculation():
    res = client.get("/api/v1/gateway/students")
    assert res.status_code == 200
    students = res.json()
    assert len(students) >= 5
    ids = [s["student_id"] for s in students]
    assert "DEMO-CSE-01" in ids
    assert "DEMO-EXHAUSTED" in ids

    cse = next(s for s in students if s["student_id"] == "DEMO-CSE-01")
    assert cse["remaining_quota_mb"] > 0
    assert cse["college_usn"] == "DEMO-USN-CSE01"
    assert cse["academic_year"] == "3rd Year"
    assert cse["is_active"] is True


def test_student_login_success():
    payload = {
        "college_usn": "DEMO-USN-CSE01",
        "student_id": "DEMO-CSE-01",
        "password": "Campus@2026",
        "client_mac": "00:50:56:c0:00:01",
        "client_ip": "192.168.214.1"
    }
    with patch("app.services.openwrt_service.OpenWrtGatewayService.authorize_client", return_value=(True, 157286, 891290)):
        res = client.post("/api/v1/gateway/login", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["gateway_authorized"] is True
        assert data["college_usn"] == "DEMO-USN-CSE01"
        assert data["student_id"] == "DEMO-CSE-01"
        assert data["remaining_quota_mb"] > 0
        assert data["upload_quota_mb"] > 0
        assert data["download_quota_mb"] > 0


def test_student_login_invalid_password():
    payload = {
        "student_id": "DEMO-CSE-01",
        "password": "WrongPassword!",
        "client_mac": "00:50:56:c0:00:01"
    }
    res = client.post("/api/v1/gateway/login", json=payload)
    assert res.status_code == 401
    assert "Invalid College USN / Student ID or password" in res.json()["detail"]


def test_student_login_nonexistent():
    payload = {
        "college_usn": "NONEXISTENT-999",
        "password": "AnyPassword",
        "client_mac": "00:50:56:c0:00:01"
    }
    res = client.post("/api/v1/gateway/login", json=payload)
    assert res.status_code == 401


def test_student_login_quota_exhausted_rejection():
    db = SessionLocal()
    st = db.query(Student).filter(Student.student_id == "DEMO-EXHAUSTED").first()
    if st:
        st.used_quota_mb = st.daily_quota_mb
        db.commit()
    db.close()

    payload = {
        "student_id": "DEMO-EXHAUSTED",
        "password": "Campus@2026",
        "client_mac": "00:50:56:c0:00:02"
    }
    res = client.post("/api/v1/gateway/login", json=payload)
    assert res.status_code == 403
    assert "Daily data quota exhausted" in res.json()["detail"]


def test_student_quota_reset():
    res = client.post("/api/v1/gateway/students/DEMO-EXHAUSTED/reset-quota")
    assert res.status_code == 200
    data = res.json()
    assert data["used_quota_mb"] == 0.0
    assert data["remaining_quota_mb"] == data["daily_quota_mb"]


def test_student_login_invalid_mac_format():
    payload = {
        "student_id": "DEMO-IT-02",
        "password": "Campus@2026",
        "client_mac": "bad-mac-format"
    }
    res = client.post("/api/v1/gateway/login", json=payload)
    assert res.status_code == 400
    assert "Invalid hardware MAC address format" in res.json()["detail"]


def test_gateway_fail_closed_on_unreachable():
    payload = {
        "student_id": "DEMO-IT-02",
        "password": "Campus@2026",
        "client_mac": "00:50:56:c0:00:03"
    }
    with patch(
        "app.services.openwrt_service.OpenWrtGatewayService.authorize_client",
        side_effect=GatewayConnectionError("Simulated OpenWrt network outage")
    ):
        res = client.post("/api/v1/gateway/login", json=payload)
        assert res.status_code == 503
        assert "Internet access was NOT granted" in res.json()["detail"]


def test_gateway_status_and_telemetry_endpoints():
    res_status = client.get("/api/v1/gateway/status")
    assert res_status.status_code == 200
    assert "gateway_connected" in res_status.json()

    res_telem = client.get("/api/v1/gateway/telemetry")
    assert res_telem.status_code == 200
    telem = res_telem.json()
    assert "active_sessions_count" in telem
    assert telem["total_demo_students"] >= 5


# =====================================================================
# Phase 3 Enhancements Tests: Admin Security, Events, USNs, OTP
# =====================================================================

def test_admin_authentication_and_protection():
    # 1. Invalid login
    res_bad = client.post("/api/v1/gateway/admin/login", json={"username": "admin", "password": "WrongPassword"})
    assert res_bad.status_code == 401

    # 2. Valid admin login
    res_ok = client.post("/api/v1/gateway/admin/login", json={"username": "admin", "password": "Admin@Campus2026"})
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["success"] is True
    assert "token" in data
    token = data["token"]

    # 3. Unauthenticated access to admin events is rejected with 401
    res_no_auth = client.get("/api/v1/gateway/admin/events")
    assert res_no_auth.status_code == 401

    # 4. Authenticated access to admin events succeeds
    res_auth = client.get("/api/v1/gateway/admin/events", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    events = res_auth.json()
    assert isinstance(events, list)
    assert len(events) >= 1  # Should contain the login event


def test_admin_create_student_and_duplicate_usn_rejection():
    # Clean up any previous test artifact
    db = SessionLocal()
    db.query(Student).filter(
        (Student.student_id == "DEMO-NEW-99") | (Student.college_usn == "DEMO-USN-NEW99")
    ).delete()
    db.commit()
    db.close()

    # Get admin token
    res_login = client.post("/api/v1/gateway/admin/login", json={"username": "admin", "password": "Admin@Campus2026"})
    token = res_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create duplicate USN
    dup_payload = {
        "college_usn": "DEMO-USN-CSE01",  # Already exists
        "student_id": "TEST-NEW-01",
        "name": "Duplicate Student",
        "department": "CSE",
        "academic_year": "2nd Year",
        "password": "Password123",
        "daily_quota_mb": 1024.0,
        "session_timeout_mins": 120
    }
    res_dup = client.post("/api/v1/gateway/admin/students", json=dup_payload, headers=headers)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

    # Create new student successfully
    new_payload = {
        "college_usn": "DEMO-USN-NEW99",
        "student_id": "DEMO-NEW-99",
        "name": "New Valid Student",
        "department": "Information Science",
        "academic_year": "1st Year",
        "password": "Password123",
        "daily_quota_mb": 1536.0,
        "session_timeout_mins": 90
    }
    res_new = client.post("/api/v1/gateway/admin/students", json=new_payload, headers=headers)
    assert res_new.status_code == 201
    st = res_new.json()
    assert st["college_usn"] == "DEMO-USN-NEW99"
    assert st["daily_quota_mb"] == 1536.0

    # Cleanup
    db = SessionLocal()
    db.query(Student).filter(Student.student_id == "DEMO-NEW-99").delete()
    db.commit()
    db.close()


def test_admin_disable_account_and_login_block():
    res_login = client.post("/api/v1/gateway/admin/login", json={"username": "admin", "password": "Admin@Campus2026"})
    token = res_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Disable student
    res_disable = client.put(
        "/api/v1/gateway/admin/students/DEMO-IT-02",
        json={"is_active": False},
        headers=headers
    )
    assert res_disable.status_code == 200
    assert res_disable.json()["is_active"] is False

    # Attempt to log in with disabled account -> rejected with 403
    res_try_login = client.post("/api/v1/gateway/login", json={
        "student_id": "DEMO-IT-02",
        "password": "Campus@2026",
        "client_mac": "00:50:56:c0:00:04"
    })
    assert res_try_login.status_code == 403
    assert "Student account is disabled" in res_try_login.json()["detail"]

    # Re-enable student
    client.put("/api/v1/gateway/admin/students/DEMO-IT-02", json={"is_active": True}, headers=headers)


def test_demo_otp_simulator_flow():
    # 1. Request demo OTP
    res_req = client.post("/api/v1/gateway/otp/request", json={"college_usn": "DEMO-USN-CSE01"})
    assert res_req.status_code == 200
    data = res_req.json()
    assert data["success"] is True
    assert "demo_otp" in data
    code = data["demo_otp"]
    assert len(code) == 6

    # 2. Login using valid demo OTP
    with patch("app.services.openwrt_service.OpenWrtGatewayService.authorize_client", return_value=(True, 157286, 891290)):
        res_login = client.post("/api/v1/gateway/login", json={
            "college_usn": "DEMO-USN-CSE01",
            "password": "Campus@2026",
            "client_mac": "00:50:56:c0:00:05",
            "otp_code": code
        })
        assert res_login.status_code == 200
        assert res_login.json()["success"] is True


def test_fas_parameter_parsing_valid():
    # Construct exact OpenNDS 10.3.1 Level 1 parameter string
    raw_str = (
        "hid=9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08, "
        "clientip=192.168.214.50, "
        "clientmac=00-0C-29-11-22-33, "
        "gatewayname=openNDS Node:000c29765ea3, "
        "gatewayaddress=192.168.214.2:2050, "
        "authdir=opennds_auth, "
        "originurl=http%3A%2F%2Fconnectivitycheck.gstatic.com"
    )
    b64_blob = base64.b64encode(raw_str.encode("utf-8")).decode("ascii")

    parsed = parse_fas_parameter(b64_blob)
    assert parsed["hid"] == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    assert parsed["clientip"] == "192.168.214.50"
    # Normalizes MAC
    assert parsed["clientmac"] == "00:0c:29:11:22:33"
    assert parsed["gatewayaddress"] == "192.168.214.2:2050"
    assert parsed["authdir"] == "opennds_auth"
    # Unquotes originurl
    assert parsed["originurl"] == "http://connectivitycheck.gstatic.com"


def test_fas_parameter_parsing_corrupted_and_empty():
    assert parse_fas_parameter(None) == {}
    assert parse_fas_parameter("") == {}
    assert parse_fas_parameter("   ") == {}
    # Corrupted base64 without crashes
    assert parse_fas_parameter("!!!not-valid-base64???") == {}
    # Incomplete padding recovery
    raw = "hid=test1234, clientip=10.0.0.1"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")
    parsed = parse_fas_parameter(b64)
    assert parsed["hid"] == "test1234"
    assert parsed["clientip"] == "10.0.0.1"


def test_fas_token_computation_against_opennds_standard():
    hid = "a1b2c3d4e5f67890"
    test_key = "secret_fas_key_2026"
    expected = hashlib.sha256((hid + test_key).encode("utf-8")).hexdigest()

    # Verified against sha256(hid . faskey)
    calculated = compute_fas_token(hid, faskey=test_key)
    assert calculated == expected

    # Test error on empty hid
    with pytest.raises(ValueError, match="Cannot compute FAS token without valid client hid"):
        compute_fas_token("")


def test_build_opennds_auth_url_formatting():
    url = build_opennds_auth_url(
        gatewayaddress="192.168.214.2:2050",
        tok="calculated_tok_12345",
        redir_url="http://connectivitycheck.gstatic.com/generate_204",
        authdir="opennds_auth"
    )
    assert url.startswith("http://192.168.214.2:2050/opennds_auth/?")
    assert "tok=calculated_tok_12345" in url
    assert "redir=" in url


def test_portal_html_rendering_for_browsers():
    raw_str = (
        "hid=browser_hid_abc123, "
        "clientip=192.168.214.77, "
        "clientmac=00:50:56:c0:00:77, "
        "gatewayaddress=192.168.214.2:2050, "
        "authdir=opennds_auth, "
        "originurl=https://www.google.com"
    )
    b64 = base64.b64encode(raw_str.encode("utf-8")).decode("ascii")

    # Request with Accept: text/html simulating mobile browser
    res = client.get(
        f"/api/v1/gateway/portal?fas={b64}",
        headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"}
    )
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html_text = res.text
    assert "Campus Wi-Fi Login" in html_text
    assert "00:50:56:c0:00:77" in html_text
    assert "192.168.214.77" in html_text
    assert "192.168.214.2:2050" in html_text
    assert 'name="college_usn"' in html_text
    assert "DEMO-USN-CSE01" in html_text
    assert "1 GiB/Day (1,024 MiB binary standard)" in html_text


def test_portal_json_fallback_for_api_clients():
    raw_str = (
        "hid=json_hid_999, "
        "clientip=192.168.214.88, "
        "clientmac=00:50:56:c0:00:88, "
        "gatewayaddress=192.168.214.2:2050"
    )
    b64 = base64.b64encode(raw_str.encode("utf-8")).decode("ascii")

    res = client.get(f"/api/v1/gateway/portal?fas={b64}&format=json")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "portal_ready"
    assert data["client_mac"] == "00:50:56:c0:00:88"
    assert data["client_ip"] == "192.168.214.88"
    assert data["hid"] == "json_hid_999"


def test_student_login_with_fas_handshake_returns_authaction():
    hid_val = "test_handshake_hid_456"
    expected_tok = hashlib.sha256((hid_val + DEFAULT_FAS_KEY).encode("utf-8")).hexdigest()

    with patch("app.services.openwrt_service.OpenWrtGatewayService.authorize_client", return_value=(True, 157286, 891290)):
        res = client.post("/api/v1/gateway/login", json={
            "college_usn": "DEMO-USN-CSE01",
            "password": "Campus@2026",
            "client_mac": "00:50:56:c0:00:91",
            "hid": hid_val,
            "gatewayaddress": "192.168.214.2:2050",
            "redir_url": "https://www.google.com"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["gateway_authorized"] is True
        assert data["tok"] == expected_tok
        assert data["authaction_url"] is not None
        assert "http://192.168.214.2:2050/opennds_auth/" in data["authaction_url"]
        assert expected_tok in data["authaction_url"]


def test_portal_form_submit_success_redirect():
    hid_val = "form_submit_hid_789"
    expected_tok = hashlib.sha256((hid_val + DEFAULT_FAS_KEY).encode("utf-8")).hexdigest()

    with patch("app.services.openwrt_service.OpenWrtGatewayService.authorize_client", return_value=(True, 157286, 891290)):
        res = client.post(
            "/api/v1/gateway/portal/submit",
            data={
                "college_usn": "DEMO-USN-CSE01",
                "password": "Campus@2026",
                "client_mac": "00:50:56:c0:00:92",
                "client_ip": "192.168.214.92",
                "hid": hid_val,
                "gatewayaddress": "192.168.214.2:2050",
                "authdir": "opennds_auth",
                "redir_url": "http://connectivitycheck.gstatic.com"
            },
            follow_redirects=False
        )
        # HTTP 303 See Other redirecting browser to OpenNDS
        assert res.status_code == 303
        loc = res.headers["location"]
        assert "http://192.168.214.2:2050/opennds_auth/" in loc
        assert f"tok={expected_tok}" in loc


def test_portal_form_submit_invalid_credentials_returns_html_error():
    res = client.post(
        "/api/v1/gateway/portal/submit",
        data={
            "college_usn": "DEMO-USN-CSE01",
            "password": "WrongPassword!999",
            "client_mac": "00:50:56:c0:00:93",
            "hid": "hid_fail_test"
        },
        follow_redirects=False
    )
    assert res.status_code == 401
    assert "text/html" in res.headers["content-type"]
    assert "Access Denied" in res.text
