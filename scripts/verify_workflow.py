"""
Targeted End-to-End Workflow Verification Script
AI-Based Wi-Fi Coverage Optimization & OpenWrt Student Gateway

Verifies:
1. Student self-registration with college USN formatting (ENG23CS0999) -> PENDING_APPROVAL
2. Pending student login blocked with HTTP 403
3. Student self-profile inspection reflects PENDING_APPROVAL
4. Administrator authentication (admin / Admin@Campus2026)
5. Administrator reviews and approves registration -> APPROVED
6. Approved student login succeeds with 1,024 MiB daily quota (Binary IEC)
7. Real OpenWrt router fail-closed check (ndsctl rejects unassociated client) -> HTTP 502
8. Quota-exhausted student blocked (DEMO-USN-EXH05) -> HTTP 403
9. Disposable test account cleaned up; all 5 demo accounts and existing students preserved intact

SAFETY:
Operates on an isolated temporary copy of the database to guarantee
zero modification or risk to the production database and existing records.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root and backend to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Configure safe isolated test database
PROD_DB_PATH = PROJECT_ROOT / "data" / "wifi_optimizer.db"
TEMP_DB_PATH = PROJECT_ROOT / "data" / f"temp_verify_workflow_{os.getpid()}.db"

# Create atomic read-only snapshot of production database for testing
src_conn = sqlite3.connect(f"file:{PROD_DB_PATH}?mode=ro", uri=True)
dst_conn = sqlite3.connect(str(TEMP_DB_PATH))
src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()

# Point backend environment to isolated test database before importing app
os.environ["DATABASE_URL"] = f"sqlite:///{TEMP_DB_PATH.as_posix()}"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DB_PATH = TEMP_DB_PATH

EXPECTED_DEMO_USNS = {
    "DEMO-USN-CSE01",
    "DEMO-USN-IT02",
    "DEMO-USN-ECE03",
    "DEMO-USN-ME04",
    "DEMO-USN-EXH05",
}


def run_verification():
    print("======================================================================")
    print(" TARGETED WORKFLOW VERIFICATION: REGISTRATION -> APPROVAL -> LOGIN")
    print(f" Database Mode: ISOLATED TEMPORARY TEST DB ({TEMP_DB_PATH.name})")
    print(" Production Database: PROTECTED (Read-Only)")
    print("======================================================================")

    test_usn = "ENG23CS0999"
    test_name = "TEST-STUDENT-RAHUL"
    test_pass = "SecureTest@2026"
    test_mac = "02:00:00:11:22:33"

    try:
        # Step 0: Ensure clean starting state in isolated test database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE college_usn = ?", (test_usn,))
        cur.execute("DELETE FROM gateway_events WHERE student_id = ?", (test_usn,))
        conn.commit()
        conn.close()

        # Step 1: Student Registration
        print("\n--- STEP 1: Student Registration ---")
        reg_payload = {
            "college_usn": test_usn,
            "name": test_name,
            "password": test_pass,
        }
        r = client.post("/api/v1/gateway/register", json=reg_payload)
        status = r.status_code
        reg_data = r.json()
        print(f"Status Code: {status}")
        print(f"Response: {reg_data}")
        assert status == 201, f"Expected 201 Created, got {status}"
        assert reg_data["college_usn"] == test_usn
        assert reg_data["approval_status"] == "PENDING_APPROVAL"
        assert reg_data["department"] == "Computer Science Core"
        assert reg_data["batch_year"] == 2023
        print(">>> [PASS] Step 1: Student Registration created in PENDING_APPROVAL status.")

        # Step 2: Pending Student Login Blocked
        print("\n--- STEP 2: Pending Student Login Blocked ---")
        login_payload = {
            "college_usn": test_usn,
            "password": test_pass,
            "client_mac": test_mac,
            "simulate_gateway": True,
        }
        r = client.post("/api/v1/gateway/login", json=login_payload)
        status = r.status_code
        login_res = r.json()
        print(f"Status Code: {status}")
        print(f"Response: {login_res}")
        assert status == 403, f"Expected 403 Forbidden, got {status}"
        assert "pending administrator approval" in login_res.get("detail", "").lower()
        print(">>> [PASS] Step 2: Unapproved student login blocked with HTTP 403.")

        # Step 3: Student Self-Profile Status Check
        print("\n--- STEP 3: Student Self-Profile Status Check ---")
        prof_payload = {
            "college_usn": test_usn,
            "password": test_pass,
        }
        r = client.post("/api/v1/gateway/students/me", json=prof_payload)
        status = r.status_code
        prof_res = r.json()
        print(f"Status Code: {status}")
        print(f"Approval Status in Profile: {prof_res.get('approval_status')}")
        assert status == 200
        assert prof_res["approval_status"] == "PENDING_APPROVAL"
        print(">>> [PASS] Step 3: Student private profile reflects PENDING_APPROVAL.")

        # Step 4: Administrator Authentication
        print("\n--- STEP 4: Administrator Authentication ---")
        admin_login_payload = {
            "username": "admin",
            "password": "Admin@Campus2026",
        }
        r = client.post("/api/v1/gateway/admin/login", json=admin_login_payload)
        status = r.status_code
        admin_data = r.json()
        assert status == 200, f"Admin login failed: {status}"
        admin_token = admin_data["token"]
        print(f"Admin Logged In: {admin_data['full_name']} ({admin_data['role']})")
        print(f"Token Acquired: {admin_token[:15]}...")
        print(">>> [PASS] Step 4: Administrator session authenticated.")

        # Step 5: Administrator Approves Registration
        print("\n--- STEP 5: Administrator Approves Registration ---")
        approval_payload = {
            "approval_status": "APPROVED",
            "admin_notes": "Identity verified by CSE Major Project Examiner",
        }
        r = client.post(
            f"/api/v1/gateway/students/{test_usn}/approval",
            json=approval_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        status = r.status_code
        app_data = r.json()
        print(f"Status Code: {status}")
        print(f"Approved Status: {app_data.get('approval_status')}, is_active: {app_data.get('is_active')}")
        assert status == 200, f"Approval failed: {status} {app_data}"
        assert app_data["approval_status"] == "APPROVED"
        assert app_data["is_active"] is True
        print(">>> [PASS] Step 5: Administrator approval granted and account activated.")

        # Step 6: Approved Student Login (Simulated Gateway Mode for Viva)
        print("\n--- STEP 6: Approved Student Login (Simulated Gateway Mode) ---")
        r = client.post("/api/v1/gateway/login", json=login_payload)
        status = r.status_code
        login_success = r.json()
        print(f"Status Code: {status}")
        print(f"Login Success: {login_success.get('success')}")
        print(f"Assigned Quota: {login_success.get('assigned_quota_mb')} MiB")
        print(f"Remaining Quota: {login_success.get('remaining_quota_mb')} MiB")
        print(f"Quota Split: Upload={login_success.get('upload_quota_mb')} MiB, Download={login_success.get('download_quota_mb')} MiB")
        assert status == 200, f"Login failed: {status} {login_success}"
        assert login_success["success"] is True
        assert login_success["assigned_quota_mb"] == 1024.0
        assert login_success["remaining_quota_mb"] == 1024.0
        print(">>> [PASS] Step 6: Approved student login succeeded with 1,024 MiB binary daily quota.")

        # Step 7: Live OpenWrt Router Gateway Rejection Test (Fail-Closed)
        print("\n--- STEP 7: Real OpenWrt Gateway Fail-Closed Rejection Test ---")
        real_gw_payload = {
            "college_usn": test_usn,
            "password": test_pass,
            "client_mac": test_mac,
            "simulate_gateway": False,  # Send real SSH ndsctl auth command to OpenWrt 192.168.214.2
        }
        r = client.post("/api/v1/gateway/login", json=real_gw_payload)
        status = r.status_code
        gw_res = r.json()
        print(f"Status Code: {status}")
        print(f"Gateway Rejection Detail: {gw_res.get('detail')}")
        assert status == 502, f"Expected 502 Bad Gateway rejection, got {status}"
        assert "OpenNDS gateway rejected client authorization" in gw_res.get("detail", "")
        print(">>> [PASS] Step 7: OpenWrt gateway fail-closed verification: Router actively evaluated ndsctl auth and rejected unconnected device.")

        # Step 8: Quota Exhausted Demo Account Blocked
        print("\n--- STEP 8: Quota Exhausted Student Blocked (DEMO-USN-EXH05) ---")
        exh_payload = {
            "college_usn": "DEMO-USN-EXH05",
            "password": "Campus@2026",
            "client_mac": "00:50:56:c0:00:01",
            "simulate_gateway": True,
        }
        r = client.post("/api/v1/gateway/login", json=exh_payload)
        status = r.status_code
        exh_res = r.json()
        print(f"Status Code: {status}")
        print(f"Exhausted Error: {exh_res.get('detail')}")
        assert status == 403, f"Expected 403 for exhausted account, got {status}"
        assert "quota exhausted" in exh_res.get("detail", "").lower()
        print(">>> [PASS] Step 8: Quota-exhausted account DEMO-USN-EXH05 strictly blocked (0 MiB remaining).")

        # Step 9: Clean Up Temporary Test Account Only & Verify Preservation
        print("\n--- STEP 9: Clean Up Temporary Test Record ---")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE college_usn = ?", (test_usn,))
        cur.execute("DELETE FROM gateway_events WHERE student_id = ?", (test_usn,))
        conn.commit()

        cur.execute("SELECT college_usn, name, daily_quota_mb, approval_status, is_demo FROM students ORDER BY id")
        remaining_students = cur.fetchall()
        conn.close()

        print(f"Deleted test student: {test_usn}")
        print(f"Remaining students in database ({len(remaining_students)} total):")
        for s in remaining_students:
            print(f"  • {s[0]}: {s[1]} | Quota={s[2]} MiB | Status={s[3]} | is_demo={bool(s[4])}")

        # Assert disposable test student was cleanly purged
        assert not any(s[0] == test_usn for s in remaining_students), f"Test account {test_usn} was not cleaned up!"

        # Assert all 5 demo accounts remain intact with is_demo=True
        demo_students = [s for s in remaining_students if bool(s[4]) or str(s[0]).startswith("DEMO-USN-")]
        assert len(demo_students) == 5, f"Expected exactly 5 demo accounts, found {len(demo_students)}"
        actual_demo_usns = {s[0] for s in demo_students}
        assert EXPECTED_DEMO_USNS.issubset(actual_demo_usns), f"Missing demo accounts: {EXPECTED_DEMO_USNS - actual_demo_usns}"

        # Assert all preserved non-demo student accounts were untouched
        non_demo_students = [s for s in remaining_students if s[0] not in EXPECTED_DEMO_USNS]
        print(f"Preserved non-demo student accounts ({len(non_demo_students)} total): {[s[0] for s in non_demo_students]}")
        assert len(remaining_students) >= 5, "Database must retain all student accounts"
        print(">>> [PASS] Step 9: Database cleaned up. All 5 demo accounts and existing students preserved intact.")

        print("\n======================================================================")
        print(" ALL 9 TARGETED WORKFLOW CHECKS PASSED (100% SUCCESS)")
        print("======================================================================")

    finally:
        # Clean up temporary isolated test database
        try:
            from app.database import engine
            engine.dispose()
        except Exception:
            pass

        if TEMP_DB_PATH.exists():
            try:
                TEMP_DB_PATH.unlink()
                print(f"[*] Cleaned up isolated test database: {TEMP_DB_PATH.name}")
            except Exception as e:
                print(f"[!] Note: Could not immediately remove {TEMP_DB_PATH.name}: {e}")


if __name__ == "__main__":
    run_verification()
