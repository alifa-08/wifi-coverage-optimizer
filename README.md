# AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System with OpenWrt-Based Student Authentication and Individual Data Quota Management

**Final-Year B.Tech Computer Science & Engineering Major Project**

---

## 1. Project Overview & Problem Statement

In university campuses, hostels, and academic blocks, Wi-Fi infrastructure and bandwidth management face two interconnected challenges:
1. **Unpredictable Physical Coverage & Dead Zones**: Heavy concrete walls, metal partitions, and suboptimal Access Point (AP) placement cause high packet loss, latency spikes, and dead zones. Network teams conventionally rely on reactive complaints or manual walk-tests.
2. **Bandwidth Abuse & Lack of Account Accountability**: Generic shared WPA2 pre-shared keys lack student accountability, dynamic admission batch verification, individual daily bandwidth limits, and administrative controls.

This major project provides a unified, production-grade engineering platform integrating:
- **Module 1: AI-Driven Wi-Fi Coverage & Dead-Zone Prediction Subsystem**: Simulates physics-informed COST-231 multi-wall RF propagation, clusters degraded spots into physical dead zones using **DBSCAN**, predicts unmeasured weak spots using a **Random Forest Machine Learning Classifier**, recommends optimized AP coordinates, and verifies quantitative dead-zone reduction through comparative Before-vs-After simulation.
- **Module 2: OpenWrt Campus Student Gateway & Individual Quota Subsystem**: Runs an embedded **OpenWrt 25.12.5** virtual router with **OpenNDS 10.3.1**, providing **Secure FAS Level 1** captive portal authentication. Validates official college USNs (`ENG23CS0518`), implements an administrative approval workflow, and strictly enforces **1 GiB (1,024 MiB)** daily binary IEC quotas with upload/download netfilter splits.
- **Module 3: Role-Separated Welcome & Demonstration Interface**: Provides a clean Welcome Landing Page with 3 distinct pathways:
  1. **Student Wi-Fi Login** (dedicated full-screen captive portal; zero admin access)
  2. **Student Registration** (onboarding with USN parsing into `PENDING_APPROVAL`)
  3. **Admin Portal** (13-page suite for student approvals, quota management, and AI maps)

---

## 2. Integrated Architecture

```
                                  CAMPUS AI WI-FI PLATFORM
                                             │
               ┌─────────────────────────────┴─────────────────────────────┐
               ▼                                                           ▼
    MODULE 1: AI RF OPTIMIZATION                                MODULE 2: OPENWRT GATEWAY
  (Multi-Wall COST-231 Physics)                              (OpenNDS 10.3.1 Captive Portal)
               │                                                           │
   [1] Survey / Simulation                                     [1] Client HTTP Intercept
   [2] DBSCAN Spatial Clustering                               [2] USN Batch/Dept Validation
   [3] Root Cause Diagnostics                                  [3] Admin Approval Workflow
   [4] Random Forest Prediction                                [4] FAS Level 1 SHA256 Token
   [5] Centroid AP Placement                                   [5] 1 GiB Binary Daily Quota
   [6] Before vs After Verification                            [6] Linux Netfilter Enforcement
               │                                                           │
               └─────────────────────────────┬─────────────────────────────┘
                                             ▼
                               MODULE 3: USER INTERFACE
                    ┌─────────────────────────────────────────┐
                    │ Welcome Landing Screen (localhost:5173) │
                    ├────────────────────┬────────────────────┤
                    │    Student View    │     Admin View     │
                    │ (Captive Portal)   │ (13-Page Suite)    │
                    └────────────────────┴────────────────────┘
```

---

## 3. Technology Stack

| Layer | Component | Version / Library | Purpose |
|---|---|---|---|
| **Frontend** | React & TypeScript | React 19, TypeScript 5.7 | Type-safe reactive web interface |
| **Styling** | Tailwind CSS & Icons | Tailwind CSS v4, Lucide React | Modern dark-mode responsive dashboard |
| **Build Tool** | Vite | Vite 8.3 | Hot module replacement & production bundling |
| **Backend** | Python & FastAPI | Python 3.11, FastAPI 0.115 | Asynchronous REST API with Pydantic v2 validation |
| **Database** | SQLite & SQLAlchemy | SQLite 3, SQLAlchemy 2.0 | Zero-config relational database with audit logs |
| **Machine Learning** | Scikit-learn | Scikit-learn 1.4 | Random Forest (100 trees), DBSCAN clustering |
| **Spatial Geometry** | SciPy Spatial & NumPy | SciPy 1.13, NumPy 1.26 | 2D Convex Hull dead-zone area calculation ($m^2$) |
| **Router OS** | OpenWrt (x86_64) | OpenWrt 25.12.5 in VMware | Campus gateway, DHCP (`192.168.214.0/24`), routing |
| **Captive Daemon**| OpenNDS | OpenNDS 10.3.1 | FAS Level 1 captive portal & netfilter traffic control |
| **Router SSH** | Paramiko | Paramiko 3.5 (Ed25519) | Programmatic headless `ndsctl` gateway execution |
| **Testing** | Pytest | Pytest 9.1 (65 Tests) | 100% automated test coverage across all subsystems |

---

## 4. Live System URLs & Ports

| Component | URL | Credentials / Notes |
|---|---|---|
| **Welcome Landing Screen** | `http://localhost:5173` | Main entrypoint for examiners and students |
| **Student Captive Portal** | `http://localhost:5173` (Student Login) | College USN + Password |
| **Admin Management Portal**| `http://localhost:5173` (Admin Portal) | Username: `admin` \| Password: `[REDACTED_ADMIN_PASSWORD]` |
| **Backend OpenAPI Docs** | `http://127.0.0.1:8000/docs` | Interactive Swagger API documentation |
| **OpenNDS Gateway Engine** | `http://192.168.214.2:2050` | OpenNDS MHD daemon on OpenWrt `br-lan` |
| **OpenWrt LuCI Web GUI** | `http://192.168.214.2:8080` | Router administrative interface |

---

## 5. How to Run the Project (Windows PowerShell)

### Step 1: Open Terminal 1 — Start FastAPI Backend
```powershell
cd "C:\path\to\Major_Project_GitHub"
.\venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
*Verify: Open `http://127.0.0.1:8000/health` in your browser. It should return `{"status":"healthy"}`.*

### Step 2: Open Terminal 2 — Start Vite Frontend
```powershell
cd "C:\path\to\Major_Project_GitHub\frontend"
npm run dev -- --host 127.0.0.1 --port 5173
```
*Verify: Open `http://localhost:5173` in your browser. The Welcome Landing Page will appear.*

### Step 3: Run the Complete Automated Test Suite (65/65 Passed)
```powershell
cd "C:\path\to\Major_Project_GitHub"
.\venv\Scripts\python -m pytest backend\tests -v
```
*All 65 tests verify API endpoints, RF path loss physics, DBSCAN clustering, Random Forest training, AP optimization, USN validation, student approvals, and FAS Level 1 tokens.*

---

## 6. Pre-Configured Demo Accounts for Viva Evaluation

| Account Type | College USN | Password | Daily Quota | Purpose / Viva Scenario |
|---|---|---|---|---|
| **Standard Student** | `DEMO-USN-CSE01` | `[REDACTED_DEMO_PASSWORD]` | 1,024 MiB (1 GiB) | Standard daily student allowance |
| **Lab Quota Student** | `DEMO-USN-IT02` | `[REDACTED_DEMO_PASSWORD]` | 2,048 MiB (2 GiB) | Extended lab research quota |
| **Research Student** | `DEMO-USN-ECE03` | `[REDACTED_DEMO_PASSWORD]` | 512 MiB | Electronics lab allowance |
| **Mechanical Student**| `DEMO-USN-ME04` | `[REDACTED_DEMO_PASSWORD]` | 256 MiB | Workshop student allowance |
| **Quota Exhausted** | `DEMO-USN-EXH05` | `[REDACTED_DEMO_PASSWORD]` | 0 MiB remaining | Tests fail-closed HTTP 403 quota exhaustion |

---

## 7. Five-Minute Viva Demonstration Sequence

1. **Welcome Landing Screen (`http://localhost:5173`)**:
   - Point out the 3 distinct pathways: Student Wi-Fi Login, Student Registration, and Admin Portal.
   - Note the live OpenWrt gateway indicator (`192.168.214.2: ONLINE`).

2. **Student Registration Workflow**:
   - Click **Student Registration**.
   - Register a student with USN `ENG23CS0518` ("Rahul Sharma").
   - Notice live USN parsing: Department = `Computer Science Core`, Admission Batch = `2023`, Academic Year = `4th Year / Final Year`.
   - Submit registration: The screen confirms `PENDING_APPROVAL` status (zero internet access until approved).

3. **Admin Approval & Quota Inspection**:
   - Click **Admin Portal** $\rightarrow$ log in with `admin` / `[REDACTED_ADMIN_PASSWORD]`.
   - Open **Student Gateway & Quotas** page.
   - Point out the amber **Pending Registrations Review** banner showing the student awaiting review.
   - Click **Approve**: Account status updates to `APPROVED` and `ACTIVE`.
   - Point out the binary IEC quota rule ($1\text{ GiB} = 1,024\text{ MiB}$) and upload/download split.

4. **Student Wi-Fi Authentication**:
   - Click **Exit Admin** $\rightarrow$ click **Student Wi-Fi Login**.
   - Click `DEMO-USN-CSE01` to quick-fill credentials.
   - Click **Connect Device to Campus Internet**.
   - System authorizes the session, displays remaining quota ($1,024.0\text{ MiB}$), directional caps ($153.6\text{ MiB}$ up, $870.4\text{ MiB}$ down), and active session ID.
   - Test quota exhaustion: Select `DEMO-USN-EXH05` $\rightarrow$ login is immediately rejected with HTTP 403.

5. **AI Wi-Fi Coverage Optimization Pipeline**:
   - Open **Admin Portal** $\rightarrow$ **Dashboard**.
   - Click **Generate Demo Environment** $\rightarrow$ select `Laboratory Dead Zone`.
   - Navigate through the 5 AI stages:
     - **Dead-Zone Analysis**: DBSCAN clusters weak signals into named polygons with exact $m^2$ affected areas.
     - **Coverage Map**: Heatmap displaying signal falloff through concrete walls.
     - **Dead-Zone Prediction**: Random Forest ML model predicting unmeasured grid points with 89% accuracy.
     - **AP Optimization**: System places recommended candidate APs at dead-zone centroids.
     - **Before vs After**: Verified dual-simulation proving $>75\%$ reduction in dead-zone area ($292\text{ m}^2 \rightarrow 68\text{ m}^2$).

---

## 8. Academic Honesty & Technical Limitations

- **Simulated vs Physical Client Testing**:
  - OpenWrt 25.12.5 runs inside VMware Workstation Pro on virtual switch `br-lan` (`VMnet1`).
  - The laptop's internal Wi-Fi card acts as an uplink receiver (WAN2 `eth2`) connected to a phone hotspot.
  - Because virtual switches cannot transmit over the air, physical smartphone redirection requires an external physical AP or USB Wi-Fi dongle bridged to `br-lan`.
  - Backend-to-router authorization via SSH (`ndsctl auth`), token calculation ($\text{tok} = \text{SHA256}(\text{hid} + \text{faskey})$), and fail-closed netfilter accounting are 100% verified live on OpenWrt 25.12.5.
