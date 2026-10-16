import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.openwrt_service import create_admin_token
from app.models.gateway import Student
from app.database import SessionLocal

client = TestClient(app)

TEST_USNS = ["ENG23CS0888", "ENG23CT0999"]

@pytest.fixture(scope="function", autouse=True)
def cleanup_test_records():
    db = SessionLocal()
    try:
        db.query(Student).filter(Student.college_usn.in_(TEST_USNS)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(Student).filter(Student.college_usn.in_(TEST_USNS)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

def test_student_registration_cs_success():
    res = client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Test Student CS",
        "password": "Password@123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["college_usn"] == "ENG23CS0888"
    assert data["department_code"] == "CS"
    assert data["batch_year"] == 2023
    assert "4th Year" in data["academic_year"]
    assert data["approval_status"] == "PENDING_APPROVAL"
    assert "pending administrator approval" in data["message"].lower()

def test_student_registration_ct_cybersecurity():
    res = client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CT0999",
        "name": "Test Student Cyber",
        "password": "Password@123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["college_usn"] == "ENG23CT0999"
    assert data["department_code"] == "CT"
    assert data["department"] == "Cybersecurity"
    assert data["approval_status"] == "PENDING_APPROVAL"

def test_student_registration_invalid_usn():
    res = client.post("/api/v1/gateway/register", json={
        "college_usn": "INVALID_USN_XYZ",
        "name": "Bad USN Student",
        "password": "Password@123"
    })
    assert res.status_code == 400
    assert "Invalid USN structure" in res.json()["detail"]

def test_student_registration_duplicate_prevention():
    # 1. Register first time
    res1 = client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Original Student",
        "password": "Password@123"
    })
    assert res1.status_code == 201

    # 2. Attempt duplicate
    res2 = client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Duplicate Student",
        "password": "Password@123"
    })
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_pending_student_login_blocked():
    # 1. Register pending student
    client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Pending Student",
        "password": "Password@123"
    })

    # 2. Login must be blocked with HTTP 403
    res = client.post("/api/v1/gateway/login", json={
        "college_usn": "ENG23CS0888",
        "password": "Password@123",
        "client_mac": "02:00:00:aa:bb:cc"
    })
    assert res.status_code == 403
    assert "pending administrator approval" in res.json()["detail"].lower()

def test_admin_approval_and_rejection_workflow():
    # 1. Register students
    client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Approval Student",
        "password": "Password@123"
    })
    client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CT0999",
        "name": "Rejection Student",
        "password": "Password@123"
    })

    admin_token = create_admin_token(username="admin", full_name="Admin", role="SUPERADMIN")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Approve ENG23CS0888
    res = client.post(
        "/api/v1/gateway/students/ENG23CS0888/approval",
        json={"approval_status": "APPROVED", "admin_notes": "Identity verified"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["approval_status"] == "APPROVED"
    assert res.json()["is_active"] is True

    # 3. Reject ENG23CT0999
    res_rej = client.post(
        "/api/v1/gateway/students/ENG23CT0999/approval",
        json={"approval_status": "REJECTED", "admin_notes": "Fake details"},
        headers=headers
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["approval_status"] == "REJECTED"
    assert res_rej.json()["is_active"] is False

    # 4. Attempt login with rejected student
    res_rej_login = client.post("/api/v1/gateway/login", json={
        "college_usn": "ENG23CT0999",
        "password": "Password@123",
        "client_mac": "02:00:00:aa:bb:cc"
    })
    assert res_rej_login.status_code == 403
    assert "rejected" in res_rej_login.json()["detail"].lower()

def test_student_self_profile_lookup():
    # 1. Register & approve student
    client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Profile Student",
        "password": "Password@123"
    })
    admin_token = create_admin_token(username="admin", full_name="Admin", role="SUPERADMIN")
    client.post(
        "/api/v1/gateway/students/ENG23CS0888/approval",
        json={"approval_status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # 2. Student checks their own private profile
    res = client.post("/api/v1/gateway/students/me", json={
        "college_usn": "ENG23CS0888",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["college_usn"] == "ENG23CS0888"
    assert data["approval_status"] == "APPROVED"
    assert data["daily_quota_mb"] == 1024.0
    assert data["remaining_quota_mb"] == 1024.0

    # 3. Wrong password fails
    res_bad = client.post("/api/v1/gateway/students/me", json={
        "college_usn": "ENG23CS0888",
        "password": "WrongPassword!"
    })
    assert res_bad.status_code == 401

def test_student_roster_filtering():
    # 1. Register student
    client.post("/api/v1/gateway/register", json={
        "college_usn": "ENG23CS0888",
        "name": "Roster Filter Student",
        "password": "Password@123"
    })

    # 2. Filter by batch_year 2023
    res_batch = client.get("/api/v1/gateway/students?batch_year=2023")
    assert res_batch.status_code == 200
    assert len(res_batch.json()) >= 1
    for s in res_batch.json():
        assert s["batch_year"] == 2023

    # 3. Filter by department_code CS
    res_cs = client.get("/api/v1/gateway/students?department_code=CS")
    assert res_cs.status_code == 200
    assert len(res_cs.json()) >= 1
    for s in res_cs.json():
        assert s["department_code"] == "CS"

    # 4. Search query
    res_search = client.get("/api/v1/gateway/students?search=ENG23CS0888")
    assert res_search.status_code == 200
    items = res_search.json()
    assert len(items) == 1
    assert items[0]["college_usn"] == "ENG23CS0888"
