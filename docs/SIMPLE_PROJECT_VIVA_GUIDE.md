# 🎓 FINAL-YEAR PROJECT VIVA & PRESENTATION GUIDE
## AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System with OpenWrt-Based Student Authentication and Individual Data Quota Management

> **Target Audience**: B.Tech Computer Science & Engineering Final-Year Student
> **Purpose**: Complete understanding of the codebase, project architecture, algorithms, gateway integration, and viva defense.
> **Key Rule**: Plain English, student-friendly explanations, zero fake buzzwords, 100% honest engineering.

---

## 📑 TABLE OF CONTENTS
1. [What is Our Project?](#1-what-is-our-project)
2. [Technologies Used & Why We Chose Them](#2-technologies-used--why-we-chose-them)
3. [How the Project Works (High-Level Architecture & Mermaid Diagram)](#3-how-the-project-works)
   - 3.1 [Integrated System Architecture](#31-integrated-system-architecture)
   - 3.2 [OpenWrt & OpenNDS 10.3.1 Student Gateway](#32-openwrt--opennds-1031-student-gateway)
   - 3.3 [College USN Validation & Department Parsing](#33-college-usn-validation--department-parsing)
   - 3.4 [Binary IEC Quota Standard (1 GiB = 1,024 MiB) & Directional Split](#34-binary-iec-quota-standard-1-gib--1024-mib--directional-split)
   - 3.5 [OpenNDS 10.3.1 FAS Level 1 Secure Handshake](#35-opennds-1031-fas-level-1-secure-handshake)
   - 3.6 [Physical AP vs USB Wi-Fi Dongle Analysis for Mobile Clients](#36-physical-ap-vs-usb-wi-fi-dongle-analysis-for-mobile-clients)
4. [Simulation Mode (Virtual RF Physics Engine)](#4-simulation-mode)
5. [Real College Survey Mode (Laptop Telemetry)](#5-real-college-survey-mode)
6. [Dead-Zone Detection (DBSCAN Clustering & Severity)](#6-dead-zone-detection)
7. [Dead-Zone Prediction (Random Forest Machine Learning)](#7-dead-zone-prediction)
8. [AP Placement Optimization & Before-vs-After Verification](#8-ap-placement-optimization)
9. [Complete Step-by-Step Workflows](#9-complete-step-by-step-workflows)
10. [Button-by-Button UI Guide ("What Happens When I Click?")](#10-button-by-button-ui-guide)
11. [Testing & Verification Suite (65/65 Passed)](#11-testing--verification-suite)
12. [Actual Results & Verification Numbers (Simulated vs Real)](#12-actual-results--verification-numbers)
13. [Honest Academic Limitations](#13-honest-academic-limitations)
14. [5-Minute Presentation Script (Integrated Spoken Demo)](#14-5-minute-presentation-script)
15. [40 Viva Questions & Simple Answers](#15-40-viva-questions--simple-answers)
16. [Quick Cheat Sheet (5-Minute Last-Minute Revision)](#16-quick-cheat-sheet)

---

## 1. WHAT IS OUR PROJECT?

### Project Title
**AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System with OpenWrt-Based Student Authentication and Individual Data Quota Management**

### What Problem Are We Solving?
In large indoor environments like college engineering blocks, hostels, libraries, and hospitals, Wi-Fi connectivity is often unpredictable. Students or staff experience sudden disconnections, slow buffering, or dropped calls in specific corners, behind thick concrete pillars, or at the edges of hallways.

Normally, network administrators troubleshoot this by either:
1. Waiting for people to file complaints.
2. Walking around blindly with a phone speed test.
3. Guessing where to install an extra Access Point (AP), which frequently causes signal interference or leaves the actual dead zone unaddressed.

### What is Our Solution?
We built an intelligent, full-stack software system that:
- Models or maps indoor building floorplans.
- Analyzes multi-parameter network quality (Signal RSSI, Ping Latency, Packet Loss, and Throughput).
- Automatically groups clustered poor spots into distinct, bounded **Dead Zones** using spatial machine learning.
- Diagnoses the physical root causes (e.g., wall attenuation vs distance vs interference).
- Uses a trained **Machine Learning classifier** to predict potential dead zones in areas that haven't even been measured yet.
- Intelligently recommends the best placement coordinates for new Access Points to eliminate dead zones.
- Mathematically verifies the improvement by providing a side-by-side **Before vs After** evaluation.

### What Does the Software Actually Do?
The software operates in two distinct operational modes:
1. **Simulation Mode**: Uses indoor radio-frequency (RF) wave propagation physics (the COST-231 multi-wall model) to simulate how radio waves pass through concrete walls, drywall, and glass partitions across a 100m × 60m campus building floor.
2. **Real College Survey Mode**: Turns any standard Windows laptop into an active survey device. A student walks around their real college campus, points to where they are on the digital floorplan, and the system extracts real hardware Wi-Fi telemetry and gateway round-trip latency.

### What is the Main Novelty?
Most commercial tools (like NetSpot or Ekahau) only draw passive, colorful heatmaps of signal strength.
Our project is novel because:
1. **Multi-Parameter Detection**: It defines a dead zone not just by weak signal (dBm), but by the combination of high latency ($>120\text{ ms}$), packet loss ($>15\%$), and dropped throughput ($<5\text{ Mbps}$).
2. **DBSCAN Spatial Clustering**: It separates isolated temporary glitches from genuine physical dead zones with polygon boundaries and $m^2$ area measurements.
3. **Predictive Machine Learning**: It uses Random Forest to extrapolate and predict dead-zone risk in unmeasured grid coordinates.
4. **Closed-Loop Optimization**: It doesn't just show problems; it provides recommended AP coordinates and verifies the dead-zone reduction percentage.

```
THE CORE WORKFLOW:
DETECT ──► UNDERSTAND ──► PREDICT ──► OPTIMIZE ──► VERIFY
```

---

## 2. TECHNOLOGIES USED & WHY WE CHOSE THEM

| Technology | Layer | Why We Used It (Student Justification) |
|---|---|---|
| **Python 3.11** | Backend Language | Standard language for data science, networking scripts, and ML modeling. Clean syntax and extensive library support. |
| **FastAPI** | Backend Web Framework | Extremely fast, modern Python asynchronous API framework. Auto-generates interactive Swagger documentation (`/docs`) and uses Pydantic for strict request validation. |
| **SQLite + SQLAlchemy** | Database & ORM | Lightweight, zero-configuration relational database. Perfect for local deployment on a laptop without needing complex PostgreSQL/MySQL background daemons. SQLAlchemy handles object-relational mapping cleanly. |
| **Scikit-learn** | Machine Learning Engine | Industry-standard ML library. We use its `RandomForestClassifier` for dead-zone prediction and `DBSCAN` for unsupervised spatial clustering. |
| **NumPy & Pandas** | Data Processing | Vectorized array operations for distance calculation, grid coordinates, and data frame manipulation. |
| **SciPy (Spatial)** | Computational Geometry | Computes the 2D **Convex Hull** polygon boundaries around dead zones and calculates exact affected floor areas ($m^2$). |
| **React 19 & TypeScript** | Frontend UI Framework | Component-based, reactive user interface with strict compile-time type safety. Ensures no null reference crashes when switching between survey points and simulated data. |
| **Vite** | Frontend Build Tool | Ultra-fast development server with instant Hot Module Replacement (HMR) and optimized static asset bundling. |
| **Tailwind CSS** | Styling | Utility-first CSS framework providing a clean, responsive, dark-mode modern dashboard UI. |
| **Lucide React** | Icons | Crisp, lightweight icons for APs, signals, alerts, metrics, and navigation. |
| **Interactive SVG / Canvas** | Floorplan Rendering | Vector rendering allows smooth zooming, real-time AP dragging, clickable pin drops, and color-coded measurement overlays without blurry pixels. |
| **Windows Native `netsh` & `ping`** | Hardware Survey Collector | Reads real Wi-Fi adapter hardware info (SSID, BSSID, RSSI, channel, link speed) and gateway round-trip latency without requiring third-party drivers or paid APIs. |
| **OpenWrt 25.12.5 (x86_64)** | Campus Network Gateway | Embedded Linux router OS running on VMware Workstation Pro. Implements firewall zones, DHCP (`192.168.214.0/24`), routing, and kernel packet filtering. |
| **OpenNDS 10.3.1** | Captive Portal Daemon | Intercepts HTTP traffic on `br-lan`, enforces FAS Level 1 authentication, tracks hardware MACs, and enforces upload/download byte quotas via kernel netfilter (`nds_mangle`). |
| **Paramiko / OpenSSH** | Secure Remote Management | Ed25519 key-based SSH automation allowing the Python FastAPI backend to execute authoritative gateway commands (`ndsctl auth`, `ndsctl deauth`, `ndsctl status`) without manual terminal intervention. |
| **Pytest** | Testing Suite | Automated backend test framework with 65 comprehensive unit and integration tests (100% pass rate) verifying API routes, physics math, DBSCAN clustering, USN parsing, student approvals, and FAS tokens. |

---

## 3. HOW THE PROJECT WORKS (HIGH-LEVEL ARCHITECTURE)

The system integrates two complementary domains into a unified engineering platform:
1. **Spatial Wi-Fi Radio Frequency (RF) Optimization & Machine Learning**: Indoor modeling, multi-wall path loss physics, DBSCAN spatial clustering, Random Forest dead-zone prediction, and automated AP placement optimization.
2. **OpenWrt-Based Campus Gateway & Individual Quota Management**: Real network gateway enforcement via OpenWrt 25.12.5 and OpenNDS 10.3.1 captive portal daemon, enforcing individual student USN validation, registration approvals, and binary IEC daily quotas (1 GiB = 1,024 MiB).

### 3.1 Integrated System Architecture

```mermaid
graph TD
    subgraph Client_Layer ["1. Client & Administrator Layer"]
        StudentDevice["Student Client / Mobile Device<br/>(HTTP Intercepted by Gateway)"]
        AdminDashboard["Network Administrator Dashboard<br/>(React 19 + TypeScript + Vite)"]
        StudentPortalUI["Student Captive Portal<br/>(Login, Self-Registration, Quota Lookup)"]
    end

    subgraph Gateway_Layer ["2. OpenWrt 25.12.5 Campus Gateway (VMware VM)"]
        br_lan["br-lan: 192.168.214.2/24<br/>(Host-Only VMnet1 LAN)"]
        OpenNDS["OpenNDS 10.3.1 Captive Daemon<br/>(MHD Server :2050 on br-lan)"]
        Netfilter["Linux Kernel Netfilter & nds_mangle<br/>(Upload & Download Byte Accounting)"]
        eth0["eth0: 192.168.162.129/24<br/>(VMware NAT Uplink to Internet)"]
        eth2["eth2: 172.20.10.4/28<br/>(Hotspot Uplink to Internet)"]
    end

    subgraph Backend_Layer ["3. Python FastAPI 0.115 Application Backend (:8000)"]
        PortalAPI["FastAPI Portal & Auth Endpoints<br/>(/api/v1/gateway/portal, /register, /login)"]
        USNEngine["USN Validation & Batch Engine<br/>(Regex: Prefix + Batch + Dept + Roll)"]
        QuotaEngine["Quota & FAS Level 1 Engine<br/>(1 GiB Split, tok = sha256(hid + faskey))"]
        GatewaySSH["Gateway SSH Remote Controller<br/>(Ed25519 Key -> ndsctl auth/deauth)"]
        RFEngine["COST-231 Multi-Wall RF Engine<br/>(Simulation of Path Loss & Obstacles)"]
        MLEngine["Scikit-Learn Machine Learning Engine<br/>(Random Forest Classifier & DBSCAN)"]
    end

    subgraph Data_Layer ["4. Persistence & Audit Layer"]
        DB[(SQLite Database: wifi_optimizer.db<br/>Students, Quotas, Sessions, Audit Ledger)]
    end

    StudentDevice -->|1. Unauthenticated HTTP Request| br_lan
    br_lan -->|2. Intercept Port 80| OpenNDS
    OpenNDS -->|3. FAS Level 1 Redirect + Query Params| PortalAPI
    PortalAPI -->|4. Render Student Captive Portal| StudentPortalUI
    StudentPortalUI -->|5. Submit USN & Password| PortalAPI
    PortalAPI -->|6. Parse & Validate USN| USNEngine
    USNEngine -->|Verify Account & Quota| DB
    PortalAPI -->|7. Authorize Client MAC via SSH| GatewaySSH
    GatewaySSH -->|ndsctl auth MAC Quota Timeout| OpenNDS
    OpenNDS -->|Configure Netfilter Chains| Netfilter
    PortalAPI -->|8. HTTP 303 Redirect tok=sha256(hid+faskey)| StudentDevice
    StudentDevice -->|9. Submit Token to Gateway| OpenNDS
    Netfilter -->|10. Routed Internet Access Allowed| eth0
    Netfilter -->|10. Routed Internet Access Allowed| eth2
    AdminDashboard -->|Manage Quotas & Approvals| PortalAPI
    PortalAPI -->|RF & Survey Analytics| RFEngine
    PortalAPI -->|Dead-Zone Predictions| MLEngine
```

---

### 3.2 OpenWrt & OpenNDS 10.3.1 Student Gateway

The campus network gateway runs on **OpenWrt 25.12.5 (x86_64)** inside VMware Workstation Pro:
- **Managed Interface (`br-lan`)**: Bound to host-only virtual adapter `VMnet1` on subnet `192.168.214.0/24`. The OpenWrt router IP is `192.168.214.2`. The Windows host IP is `192.168.214.1`.
- **Uplink Interfaces**:
  - `eth0`: VMware NAT adapter (`192.168.162.129/24`) connecting to the host's internet.
  - `eth2`: Bridged adapter (`172.20.10.4/28`) providing redundant hotspot connectivity.
- **OpenNDS 10.3.1**: Kernel-level captive daemon listening on port `2050`. It intercepts unauthorized HTTP web requests from client devices, redirects them to the FAS portal on the Windows host (`http://192.168.214.1:8000/api/v1/gateway/portal`), and guards access until authorized via `ndsctl auth`.
- **Management Protection**: The Windows host MAC address (`00:50:56:C0:00:01`) is configured as a `trustedmac` in `/etc/config/opennds`. This ensures LuCI web management (ports 8080 and 443) and SSH management are never blocked or captured.

---

### 3.3 College USN Validation & Department Parsing

Every student accessing the campus network is identified by their official College University Seat Number (USN). The system implements an automated regex validation and parsing engine:
- **USN Format**: `^[A-Za-z]{3}\d{2}[A-Za-z]{2}\d{3,5}$`
  - **3-Letter Institution Prefix**: e.g., `ENG` (Engineering College).
  - **2-Digit Batch Year**: e.g., `23` maps to admission year `2023`; `24` maps to `2024`.
  - **2-Letter Department Code**: e.g., `CS` (Computer Science & Engineering), `CT` (Computer Technology / Cybersecurity), `IT` (Information Technology), `EC` (Electronics & Communication), `ME` (Mechanical Engineering).
  - **3 to 5 Digit Roll Number**: e.g., `0518`, `0112`.
- **Examples**:
  - `ENG23CS0518` $\rightarrow$ Year: 2023, Department: Computer Science, Roll: 0518. In 2026, academic year is **4th Year / Final Year** ($2026 - 2023 = 3$).
  - `ENG23CT0112` $\rightarrow$ Year: 2023, Department: Computer Technology (Cybersecurity), Roll: 0112. In 2026, academic year is **4th Year / Final Year**.
  - `ENG24CS0518` $\rightarrow$ Year: 2024, Department: Computer Science, Roll: 0518. In 2026, academic year is **3rd Year** ($2026 - 2024 = 2$).
- **Registration Workflow**:
  1. Student fills out the Captive Portal registration form with their USN, full name, and password.
  2. The backend validates USN syntax and confirms no duplicate account exists.
  3. The initial account status is set to `PENDING_APPROVAL`.
  4. Internet access is **strictly blocked (fail-closed)** until an administrator reviews and approves the account in the Gateway Management console.

---

### 3.4 Binary IEC Quota Standard (1 GiB = 1,024 MiB) & Directional Split

To ensure fair bandwidth distribution across the college campus, every authenticated student receives a daily quota based on the **IEC Binary Standard**:
$$\text{Standard Daily Allowance} = 1\text{ GiB} = 1,024\text{ MiB} = 1,048,576\text{ KiB}$$

- **Why Binary IEC Instead of Decimal SI?**
  In computer networking and operating system memory, powers of 2 ($2^{10} = 1,024$, $2^{20} = 1,048,576$) govern buffer allocation and packet byte counters. Using decimal SI ($1,000\text{ MB}$) creates accounting discrepancies between the router netfilter counters and the database.
- **Directional Split to Prevent Accidental Double Allocation**:
  OpenNDS enforces quotas as distinct upload and download arguments:
  ```bash
  ndsctl auth <client_mac> <session_timeout_mins> <upload_quota_kb> <download_quota_kb>
  ```
  If a student has a remaining quota of $1,024\text{ MiB}$, setting upload = $1,024\text{ MiB}$ and download = $1,024\text{ MiB}$ would accidentally allow the student to transfer up to $2,048\text{ MiB}$ ($2\text{ GiB}$) in total!
  To prevent this quota leak, our backend calculates a balanced directional split:
  $$\text{Upload Cap} = \frac{\text{Remaining MiB}}{2} = 512\text{ MiB} \quad (524,288\text{ KiB})$$
  $$\text{Download Cap} = \frac{\text{Remaining MiB}}{2} = 512\text{ MiB} \quad (524,288\text{ KiB})$$
  $$\text{Total Enforced Allowance} = 512\text{ MiB} + 512\text{ MiB} = 1,024\text{ MiB} = 1\text{ GiB}$$
- **Daily Reset**: Every night at midnight (or upon administrative override), consumed data resets to $0.0\text{ MiB}$, restoring the full $1,024\text{ MiB}$ quota.

---

### 3.5 OpenNDS 10.3.1 FAS Level 1 Secure Handshake

OpenNDS supports multiple Forwarding Authentication Service (FAS) modes. Our system implements **Secure FAS Level 1**:

1. **Interception**: A student device connects to the campus Wi-Fi and attempts to browse `http://neverssl.com`.
2. **Gateway Redirection**: OpenNDS intercepts the TCP port 80 request and redirects the browser to the backend:
   ```
   http://192.168.214.1:8000/api/v1/gateway/portal?fas=<base64_blob>&hid=<hid>&gatewayaddress=192.168.214.2:2050&authdir=opennds_auth&originurl=http://neverssl.com
   ```
3. **Portal Presentation**: FastAPI serves an accessible HTML captive portal displaying the client's detected hardware MAC, IP, gateway address, and USN login fields.
4. **Credential & Status Verification**:
   - Checks if USN exists in SQLite.
   - Verifies `approval_status == 'APPROVED'`. (If `PENDING_APPROVAL`, HTTP 403 is returned with a clear alert).
   - Verifies PBKDF2-HMAC-SHA256 password hash.
   - Verifies remaining quota $> 0\text{ MiB}$.
5. **Gateway Authorization via SSH**:
   FastAPI connects to OpenWrt via SSH using an ed25519 key and issues:
   ```bash
   ndsctl auth 00:11:22:33:44:55 120 524288 524288
   ```
6. **Cryptographic Token Computation**:
   OpenNDS Level 1 requires the backend to compute a SHA256 signature using the client's gateway session hash ID (`hid`) and the pre-shared secret key (`faskey`):
   $$\text{tok} = \text{SHA256}(\text{hid} + \text{faskey})$$
7. **Browser Redirect Completion**:
   The backend issues an HTTP 303 See Other redirect back to the OpenWrt gateway MHD server:
   ```
   http://192.168.214.2:2050/opennds_auth/?tok=<tok>&redir=http://neverssl.com
   ```
8. **Internet Unlocked**: OpenNDS validates the token, configures netfilter `nds_mangle` rules for the client's MAC and IP, and forwards the browser to the target destination.

---

### 3.6 Physical AP vs USB Wi-Fi Dongle Analysis for Mobile Clients

During the project defense, examiners often ask:
*"Why does a phone need an external Access Point or USB Wi-Fi dongle to test real captive portal redirection?"*

Here is the exact networking reality:
1. **The Laptop's Internal Wi-Fi Card is an Uplink**:
   The laptop's built-in Wi-Fi card connects to an existing router or iPhone hotspot (WAN2 `eth2`). It acts as a **client receiver**, not as a Wi-Fi transmitter or AP.
2. **OpenWrt LAN Interface (`br-lan`) is Virtual**:
   Inside VMware, `br-lan` (`192.168.214.2`) is connected to the host-only virtual switch `VMnet1`. It has no direct physical radio antenna to broadcast an SSID over the air.
3. **The Two Hardware Options for Connecting Student Smartphones**:
   - **Option A: Physical Wi-Fi Access Point (Recommended for Production)**:
     Connect a standard physical Wi-Fi router or AP (e.g., TP-Link / Netgear) to the laptop's RJ-45 Ethernet port. Bridge that Ethernet adapter into VMware `br-lan`. The AP broadcasts the SSID `"Campus-Student-WiFi"`. Any smartphone connecting to this SSID receives an IP from OpenWrt (`192.168.214.x`) and is instantly intercepted by OpenNDS.
   - **Option B: USB Wi-Fi Dongle (Recommended for Lab Demos)**:
     Plug an external USB Wi-Fi adapter into the laptop, attach it directly to the OpenWrt virtual machine in VMware (`VM > Removable Devices > Connect`), configure `hostapd` inside OpenWrt, and broadcast the captive SSID directly from the virtual router.
4. **Academic Honesty Distinction**:
   - **Gateway-to-Backend FAS Authorization (`ndsctl auth`)**: 100% verified, live, and operational.
   - **Simulated Client Authentication**: Fully automated via test suite and portal UI.
   - **Physical Mobile Phone Redirection**: Requires dedicated hardware bridging (Option A or B) because virtual switches cannot broadcast over the air.

---

### The 9 Integrated Operational Steps:
1. **Floorplan Modeling**: Load architectural walls (concrete, drywall, glass) and AP locations.
2. **Telemetry Acquisition**: Collect RF measurements via COST-231 simulation or laptop Windows survey (`netsh`/`ping`).
3. **Dead-Zone Clustering (DBSCAN)**: Cluster multi-parameter degraded points into convex hull dead zones with $m^2$ area measurements.
4. **ML Risk Prediction**: Train Random Forest classifier to predict unmeasured dead-zone risks across the building.
5. **AP Optimization**: Compute candidate AP locations at dead-zone centroids and verify Before-vs-After area reduction.
6. **Gateway Interception**: OpenWrt OpenNDS daemon intercepts student HTTP web traffic on `br-lan`.
7. **Student Registration & USN Parsing**: Validate USN regex, extract batch year and department, and create account with `PENDING_APPROVAL`.
8. **Administrator Approval**: Admin reviews registrations, sets quota, and activates account in Gateway Management console.
9. **FAS Authorization & Quota Accounting**: Authenticate student, split $1\text{ GiB}$ quota into upload/download netfilter caps, compute SHA256 token, and log immutable audit event.

---

## 4. SIMULATION MODE

### What Data is Generated?
In Simulation Mode, the system generates a grid of virtual measurement points across the floor (e.g., spaced every 2 to 3 meters). For each point $(x, y)$, it records:
- **RSSI** (Received Signal Strength Indicator in dBm)
- **Ping Latency** (round-trip time in milliseconds)
- **Packet Loss** (percentage of dropped packets, 0–100%)
- **Throughput** (estimated bandwidth in Mbps)
- **Quality Category** (GOOD, MODERATE, or POOR)
- **Distance to Nearest AP** (in meters)
- **Wall Attenuation Factor** (cumulative dB loss through intersected walls)

### How is the Physics Modeled? (The Math)
We implemented the **Multi-Wall COST-231 Indoor Propagation Model** (also aligned with ITU-R P.1238):

$$PL(d) = PL(d_0) + 10 \cdot n \cdot \log_{10}\left(\frac{d}{d_0}\right) + \sum_{i=1}^{W} WAF_i + X_\sigma$$

Where:
- $PL(d)$ is the total path loss at distance $d$.
- $PL(d_0)$ is the reference path loss at 1 meter (set to $40\text{ dB}$ for $2.4\text{ GHz}$).
- $n$ is the indoor path loss exponent (set to $3.0$ for multi-partition office/academic environments).
- $d$ is Euclidean distance: $\sqrt{(x - x_{AP})^2 + (y - y_{AP})^2}$.
- $\sum WAF_i$ is the Wall Attenuation Factor: the cumulative loss of all walls directly intersecting the straight-line ray from the AP to the receiver:
  - **Concrete Wall**: $12\text{ dB}$ to $15\text{ dB}$ loss
  - **Drywall / Brick**: $6\text{ dB}$ to $8\text{ dB}$ loss
  - **Glass Partition**: $2\text{ dB}$ to $3\text{ dB}$ loss
- $X_\sigma$ is log-normal shadowing noise: a Gaussian random variable $\mathcal{N}(0, \sigma^2)$ representing unpredictable multi-path fading ($\sigma = 1.8\text{ dB}$).

Finally, received signal is:
$$RSSI = P_{tx} - PL(d)$$
Where $P_{tx}$ is the AP transmit power (typically $+20\text{ dBm}$ / $100\text{ mW}$).

### Correlated Network Performance Metrics
Signal strength directly dictates network performance. We model this physical relationship realistically:
- **Good Signal ($RSSI \ge -65\text{ dBm}$)**:
  Low latency ($10–25\text{ ms}$), negligible packet loss ($0–1\%$), high throughput ($100–250\text{ Mbps}$).
- **Moderate Signal ($-65\text{ dBm} > RSSI \ge -78\text{ dBm}$)**:
  Moderate latency ($35–80\text{ ms}$), minor packet loss ($2–6\%$), usable throughput ($30–75\text{ Mbps}$).
- **Poor Signal ($RSSI < -78\text{ dBm}$)**:
  Wi-Fi adapter drops to basic modulation schemes (BPSK), retransmissions spike. Latency jumps to $120–400\text{ ms}$, packet loss climbs to $15–50\%$, throughput collapses below $5\text{ Mbps}$.

### Why is this Called "Simulated Data"?
Because no physical radio antennas are being measured during this mode. The data is generated purely mathematically inside Python using established RF physics equations and 2D ray-intersection geometry. This allows testing building layouts before physical construction or deployment.

---

## 5. REAL COLLEGE SURVEY MODE

### How Does the Laptop Collect Real Wi-Fi Info?
In Real College Survey Mode, the Python backend executes native Windows operating system commands directly on the user's laptop:

1. **Wi-Fi Telemetry via `netsh`**:
   The backend executes:
   ```cmd
   netsh wlan show interfaces
   ```
   and parses the output using regular expressions (`re`).

2. **Network Latency & Packet Loss via `ping`**:
   The backend automatically identifies the laptop's local default IPv4 gateway (the Wi-Fi router IP, e.g., `192.168.1.1` or `172.20.10.1`) using PowerShell (`Get-NetRoute`) or `ipconfig`.
   It then sends 3 ICMP echo requests:
   ```cmd
   ping -n 3 -w 1000 <GATEWAY_IP>
   ```

### Why Ping the Local Gateway Instead of Google (`8.8.8.8`)?
> **Key Viva Point**: If you ping `google.com` or `8.8.8.8`, your latency includes the college ISP fiber line, external internet congestion, and DNS resolution. Pinging the **local default gateway** isolates the **first-hop wireless link**, measuring purely the laptop-to-AP radio performance!

### What Information is Collected?
- **SSID**: Service Set Identifier (network name, e.g., `Campus_WiFi_5G`).
- **BSSID**: Physical MAC address of the specific Access Point radio the laptop is connected to (e.g., `a2:a4:e4:13:06:a7`).
- **Radio Standard**: E.g., `802.11ac` (Wi-Fi 5) or `802.11ax` (Wi-Fi 6).
- **Band & Channel**: E.g., $5\text{ GHz}$, Channel $149$.
- **Signal Percentage**: 0% to 100% reported by the Windows WLAN API.
- **RSSI (dBm)**: Hardware RSSI if exposed by the driver, or calculated via standard Microsoft formula.
- **Link Speed**: Current physical modulation rate (e.g., `866 Mbps` or `1201 Mbps`).
- **Gateway Round-Trip Latency**: Average ping time in milliseconds.
- **Packet Loss**: Percentage of dropped packets ($0\%$, $33\%$, $66\%$, or $100\%$).
- **Timestamp**: Exact UTC capture time.
- **Floorplan Coordinates**: User-selected $(x, y)$ position in meters.

### How Does the User Select Location on the Floorplan?
1. The student walks to a physical spot on their campus (e.g., "Library Room 102, back desk").
2. On the Real Survey page, the student looks at the digital floorplan and clicks that exact spot.
3. The UI places a visual **Target Pin** (crosshair indicator) and shows the exact coordinates: $X = 14.5\text{ m}, Y = 8.2\text{ m}$.
4. (Optional) The student can also click quick-pick room chips like `[Room 101]` or `[Auditorium]` to auto-position the pin.
5. The student clicks **"Capture Measurement at Pin"**.

### Real vs Estimated Values (Honest Technical Transparency)

| Metric | Source | Real Hardware or Derived? |
|---|---|---|
| **SSID & BSSID** | Windows `netsh wlan show interfaces` | **100% Real Hardware Telemetry** |
| **Radio Type, Band, Channel** | Windows `netsh wlan show interfaces` | **100% Real Hardware Telemetry** |
| **Signal %** | Windows `netsh wlan show interfaces` | **100% Real Hardware Telemetry** |
| **Link Speed (Tx/Rx rate)** | Windows `netsh wlan show interfaces` | **100% Real Hardware Telemetry** |
| **Ping Latency & Packet Loss** | Native ICMP ping to default gateway | **100% Real Network Telemetry** |
| **RSSI (dBm)** | Hardware driver (if supported) OR formula `(Signal% / 2) - 100` | Real if driver supports; clearly tagged with `is_rssi_estimated: True/False` |
| **Throughput** | Derived from physical link speed (Rx/Tx) | Estimated operational bandwidth (we do not run a full iperf saturating bandwidth) |

---

## 6. DEAD-ZONE DETECTION

### What is a Wi-Fi Dead Zone?
A dead zone is not just a spot with low bars. In our system, a dead zone is defined as:
> **A continuous spatial region where network degradation prevents reliable communication, characterized by severe signal attenuation, excessive round-trip latency, high packet loss, or collapsed throughput.**

### Multi-Metric Poor Point Thresholds
A measurement point is flagged as **POOR** if it meets ANY of these conditions:
1. $RSSI < -78.0\text{ dBm}$ (Signal too weak for stable QAM modulation)
2. $\text{Ping Latency} > 120.0\text{ ms}$ (Excessive buffer delay / retries)
3. $\text{Packet Loss} > 15.0\%$ (Frequent TCP retransmissions & dropped connections)
4. $\text{Throughput} < 5.0\text{ Mbps}$ (Insufficient bandwidth for video/voice)

### Spatial Clustering: Why DBSCAN?
We use **DBSCAN** (*Density-Based Spatial Clustering of Applications with Noise*).

```
Parameters used:
• eps (epsilon) = 6.0 to 12.0 meters (maximum distance between neighbor points)
• min_samples   = 3 points (minimum points to constitute a real dead zone)
```

**Why DBSCAN instead of K-Means?**
1. **We don't know the number of clusters in advance**: K-Means requires specifying $K$ (e.g., $K=3$). In a building, we have no idea whether there are 0, 2, or 5 dead zones. DBSCAN discovers the number of clusters automatically.
2. **Arbitrary shapes**: Dead zones follow corridors or odd room corners. K-Means assumes spherical clusters; DBSCAN can find any arbitrary shape.
3. **Noise Handling**: If a single measurement drops due to someone walking by, DBSCAN labels it as **noise** (label `-1`) and discards it! **A single bad measurement never creates a false dead zone.**

### How Does a Cluster Become a Dead-Zone Area?
When DBSCAN identifies a cluster of $\ge 3$ poor points:
1. **Centroid**: Computes $(\bar{x}, \bar{y})$ average center coordinate.
2. **Convex Hull Boundary**: Runs the Graham scan 2D convex hull algorithm to form a closed polygon around the perimeter points.
3. **Area Calculation ($m^2$)**: Applies the Shoelace formula on the polygon vertices:
   $$\text{Area} = \frac{1}{2} \left| \sum_{i=1}^{n-1} (x_i y_{i+1} - x_{i+1} y_i) + (x_n y_1 - x_1 y_n) \right|$$
   Bounded by grid cell coverage ($N_{points} \times 4\text{ m}^2$).
4. **Severity Scoring**: Computes a multi-metric composite penalty score (0–100):
   - $\ge 75 \rightarrow$ **CRITICAL**
   - $52 - 74 \rightarrow$ **HIGH**
   - $32 - 51 \rightarrow$ **MEDIUM**
   - $< 32 \rightarrow$ **LOW**
5. **Contributing Factor Diagnosis**: The system inspects average wall loss, distance, and packet loss to output human-readable causes (e.g., *"Severe wall attenuation: 24.0 dB loss through multiple concrete partitions"*).

---

## 7. DEAD-ZONE PREDICTION (MACHINE LEARNING)

### What Model is Used?
We use a **Random Forest Classifier** (`RandomForestClassifier` from Scikit-learn):
- **Ensemble Size**: 100 decision trees (`n_estimators = 100`)
- **Max Depth**: 12 levels (`max_depth = 12`)
- **Class Weighting**: Balanced (`class_weight = "balanced"`) to handle class imbalance between normal areas and dead zones.

### Why Random Forest?
1. **Non-linear Relationships**: Wi-Fi propagation and obstacle penetration are non-linear; decision trees model threshold cutoffs naturally.
2. **Robust Against Overfitting**: Combining 100 randomized trees via bagging prevents the model from overfitting to isolated noise.
3. **Feature Importance**: Random Forest automatically tells us *which* network features had the biggest influence on predicting dead zones.
4. **Fast Inference**: Can predict hundreds of unmeasured spatial grid points in under 50 milliseconds.

### Input Features & Target Label

| Feature Name | Description |
|---|---|
| `rssi` | Signal strength in dBm |
| `latency` | Ping latency in milliseconds |
| `packet_loss` | Packet loss percentage |
| `throughput` | Estimated or measured data rate in Mbps |
| `distance_to_ap` | Distance to closest operational AP in meters |
| `wall_factor` | Cumulative wall attenuation along line-of-sight |
| `ap_density` | Count of operational APs within a 25-meter radius |

**Target Label (`dead_zone_risk`)**:
- `0`: `NOT_DEAD_ZONE` (Healthy network area)
- `1`: `POTENTIAL_DEAD_ZONE` (High-risk weak area)

### Evaluation Metrics Explained in Plain English

```
                          ACTUAL DEAD ZONE    ACTUAL HEALTHY
PREDICTED DEAD ZONE       True Positive (TP)  False Positive (FP)
PREDICTED HEALTHY         False Negative (FN) True Negative (TN)
```

- **Accuracy** ($\frac{TP + TN}{\text{Total}}$): Overall percentage of correct predictions across all test points (typically **~88%–92%**).
- **Precision** ($\frac{TP}{TP + FP}$): *"When the model predicts an area is a dead zone, how often is it actually right?"* (Prevents wasting money installing APs where signal is actually fine).
- **Recall** ($\frac{TP}{TP + FN}$): *"Out of all real dead zones in the building, how many did the model catch?"* (High recall ensures no dead zones are missed).
- **F1-Score** ($2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$): Harmonic mean of precision and recall. Best single metric for balanced performance.
- **Confusion Matrix**: A $2 \times 2$ grid showing exact counts of TP, FP, FN, and TN.
- **Feature Importance**: Ranked percentages showing what mattered most (e.g., `rssi` ~38%, `distance_to_ap` ~24%, `wall_factor` ~18%).

### Training Data Ground Truth
The model is trained on a physics-consistent dataset generated using our COST-231 multi-scenario corpus (or historical survey records if $\ge 200$ points are available). Ground truth is assigned using composite multi-variable degradation rules, ensuring the model learns complex multi-feature patterns rather than a simple 1D cutoff.

---

## 8. AP PLACEMENT OPTIMIZATION

### How Does the System Suggest New AP Locations?
When dead zones are detected, the optimizer doesn't just guess a random spot:
1. **Candidate Generation**:
   - Primary candidate: The exact centroid $(\bar{x}, \bar{y})$ of each detected dead-zone polygon.
   - Secondary candidate: Centroids of affected rooms containing dead zones.
   - Minimum separation constraint: Ensures candidates are at least $12\text{ meters}$ away from existing APs to prevent co-channel interference.
2. **Physics Re-Simulation**:
   The engine virtually adds each candidate AP (at $+20\text{ dBm}$ transmit power) to the floor's AP list and re-runs the RF path loss calculation across the entire floor.
3. **Ranking by Impact**:
   Candidates are ranked by:
   - **Dead-Zone Area Reduction ($m^2$)**: How much dead-zone space is wiped out.
   - **Coverage Improvement (%)**: Floor area brought above $-75\text{ dBm}$.
4. **Before vs After Verification**:
   The system calculates the exact delta:
   $$\text{Dead Zone Reduction \%} = \frac{\text{Area}_{before} - \text{Area}_{after}}{\text{Area}_{before}} \times 100$$

---

## 9. COMPLETE STEP-BY-STEP WORKFLOWS

### Workflow A: Simulation Mode (Demo Walkthrough)
1. Navigate to **Simulation** page.
2. Click **"Load Default Virtual Environment"** (creates 100m × 60m campus floor with 8 rooms, 3 active APs, and multiple walls).
3. Click **"Run Full Wi-Fi Simulation"** (calculates signal & network metrics across 100+ grid points).
4. Navigate to **Dead-Zone Analysis** page.
5. Click **"Run Dead-Zone Detection"** (DBSCAN clusters weak points, draws red convex hulls, displays severity & factors).
6. Navigate to **Dead-Zone Prediction** page.
7. Click **"Train Random Forest Model"** (trains on dataset, displays Accuracy, Precision, Recall, Confusion Matrix).
8. Click **"Run Spatial Grid Prediction"** (evaluates all unmeasured floor coordinates and overlays orange risk markers).
9. Navigate to **AP Optimization** page.
10. Click **"Generate AP Recommendations"** (suggests optimal placement coords).
11. Navigate to **Before vs After** page to inspect the comparative reduction metrics and side-by-side floorplans.

### Workflow B: Real College Survey Mode (Walk-Through with Laptop)
1. Open the application on your laptop (connected to your college Wi-Fi).
2. Navigate to **Real College Survey** page.
3. Select the building floor (e.g., `Engineering Block - Floor 1`).
4. Walk to a physical location inside the building (e.g., Room 104).
5. Click that spot on the digital floorplan (Target Pin appears with coordinates).
6. Click **"Capture Measurement at Pin"**.
7. The system queries `netsh` and pings the default gateway. A green notification confirms capture:
   *`Captured at (35.0, 18.0) | SSID: Campus_WiFi | Signal: 68% | Latency: 22ms`*
8. Walk to 10–15 different spots across the floor (including rooms, hallways, and corners) and repeat.
9. Click **"Export Survey Data as CSV"** to save your physical survey dataset.
10. Click **"Analyze Survey Dead Zones"** to run DBSCAN and ML on your real-world measurements!

---

## 10. BUTTON-BY-BUTTON UI GUIDE

| Page | Button Label | Internal Backend Action | Visual Result on Screen |
|---|---|---|---|
| **Simulation** | *Load Default Virtual Environment* | `POST /api/simulation/reset-demo` | Wipes previous data and loads standard campus building with rooms, walls, and 3 APs. |
| **Simulation** | *Run Full Wi-Fi Simulation* | `POST /api/simulation/run` | Runs COST-231 path loss on grid; writes ~100 measurement rows to database. | Floorplan fills with color-coded circles (Green = Good, Yellow = Moderate, Red = Poor). |
| **Dead-Zone Analysis** | *Detect Dead Zones* | `POST /api/dead-zones/detect` | Runs DBSCAN clustering ($\epsilon=6\text{m}$, $min\_samples=3$); computes convex hulls & severity. | Outlines red dead-zone polygons on floorplan with labels (DZ-1, DZ-2) and severity badges. |
| **Dead-Zone Prediction** | *Train Prediction Model* | `POST /api/ml/train` | Trains Scikit-learn Random Forest (100 trees); saves `joblib` file; calculates evaluation metrics. | Displays Accuracy, Precision, Recall, F1 cards, Confusion Matrix table, and Feature Importance bar chart. |
| **Dead-Zone Prediction** | *Predict Unmeasured Grid* | `POST /api/ml/predict-floor` | Feeds spatial grid into trained model; classifies risk probability. | Overlays orange warning dots on high-risk unmeasured zones. |
| **AP Optimization** | *Generate Recommendations* | `POST /api/optimizer/recommend` | Evaluates dead-zone centroids; simulates candidate AP coverage; ranks top placements. | Shows suggested AP coordinates (e.g., $X=72.5\text{m}, Y=38.0\text{m}$) with expected area reduction in $m^2$. |
| **Before vs After** | *Run Verification* | `GET /api/optimizer/before-after` | Compares pre-optimization run with simulated post-optimization run. | Side-by-side floorplans; metric comparison cards showing dead zones reduced (e.g., $4 \rightarrow 1$) and % reduction. |
| **Real Survey** | *Click on Floorplan* | Client-side state update | Sets $(X, Y)$ target coordinates; moves Target Pin crosshair. | Crosshair pin appears on map; coordinate badge updates (e.g., `X: 24.0m, Y: 12.5m`). |
| **Real Survey** | *Capture Measurement* | `POST /api/survey/measurements` | Executes `netsh wlan show interfaces` and pings local gateway; stores real row in DB. | Measurement pin added to map; real metrics table updates; audio/visual confirmation banner appears. |
| **Real Survey** | *Export CSV* | Client-side CSV generation | Fetches all survey measurements and triggers browser file download. | Downloads `survey_measurements_floor_X.csv` to user's computer. |
| **Campus Gateway** | *Admin Login* | `POST /api/v1/gateway/admin/login` | Validates admin credentials; generates JWT bearer token. | Unlocks sensitive controls (Add Student, Edit Quota, Disable Account, Deauth Client). |
| **Campus Gateway** | *Approve / Reject Student* | `POST /api/v1/gateway/students/{id}/approval` | Sets status to `APPROVED` or `REJECTED`; activates/deactivates netfilter access. | Moves student from Pending Review banner to active roster; logs security event. |
| **Campus Gateway** | *Disconnect Client* | `POST /api/v1/gateway/admin/deauth/{mac}` | Executes `ndsctl deauth <mac>` over SSH to OpenWrt gateway. | Terminates live connection; removes client from live netfilter table. |
| **Campus Gateway** | *Reset Quota* | `POST /api/v1/gateway/admin/students/{id}/reset-quota` | Resets consumed data to $0.0\text{ MiB}$; updates reset date to today. | Resets quota progress bar to 100% full ($1,024\text{ MiB}$ available). |
| **Student Portal** | *Authenticate & Connect* | `POST /api/v1/gateway/login` & `POST /portal/submit` | Verifies USN, password, and quota; triggers OpenWrt `ndsctl auth`; computes SHA256 FAS token. | Authorizes device; redirects browser to requested origin URL or Google. |
| **Student Portal** | *Submit Registration* | `POST /api/v1/gateway/register` | Validates USN regex; parses batch year and dept; sets status `PENDING_APPROVAL`. | Displays confirmation banner; informs student that admin approval is required. |
| **Student Portal** | *Check My Usage* | `POST /api/v1/gateway/students/me` | Authenticates student credentials; retrieves own remaining quota and sessions. | Displays private quota progress bar, reset schedule, and session history (zero data leaks). |

---

## 11. TESTING & VERIFICATION SUITE

The project includes an automated test suite using **Pytest**:

```bash
cd backend
..\venv\Scripts\python.exe -m pytest tests -v
```

### Test Suite Summary: **65 Passed / 0 Failed (100% Pass Rate)**

| Test File | Test Count | What It Verifies |
|---|---|---|
| `test_api.py` | 6 tests | Health check, API demo reset, dashboard summary, dead-zone analytics, ML metrics, alerts endpoint. |
| `test_dead_zone_detection.py` | 3 tests | Multi-metric severity logic (LOW to CRITICAL), contributing factor diagnosis, DBSCAN spatial clustering. |
| `test_ml_pipeline.py` | 2 tests | Synthetic corpus generation, Random Forest training, evaluation metrics generation, joblib persistence. |
| `test_optimizer.py` | 1 test | AP recommendation candidate generation, dead-zone area reduction calculation, before-vs-after schema. |
| `test_simulation.py` | 4 tests | RF physics path loss vs distance, wall attenuation loss, network metric correlation, geometry ray intersection. |
| `test_survey.py` | 5 tests | Hardware RSSI parsing, signal percentage fallback formula, ping latency parsing, quality scoring, survey REST endpoints. |
| `test_usn_validation.py` | 9 tests | Real college USN formats (`ENG23CS0518`, `ENG23CT0112`), batch year mapping, dynamic academic year calculation in 2026, demo USN flags, invalid format rejections. |
| `test_student_portal.py` | 8 tests | Student self-registration (CS and CT branches), duplicate USN rejection (HTTP 409), pending approval blocking (HTTP 403), admin approval/rejection lifecycle, private self-lookup, department/batch roster filtering. |
| `test_gateway.py` | 27 tests | Gateway status/telemetry, password hashing (PBKDF2-HMAC-SHA256), MAC normalization, quota split math (upload/download), `ndsctl` command construction, FAS Level 1 query parameter parsing, token computation ($\text{tok} = \text{sha256}(\text{hid} + \text{faskey})$), HTML portal rendering, fail-closed behavior on unreachable gateway, admin authentication, OTP simulator. |

### Frontend Build Verification
The React 19 / TypeScript frontend compiles cleanly with zero errors:
```bash
cd frontend
npm run build
# Output: ✓ built in 694ms (dist ready for production deployment)
```

---

## 12. ACTUAL RESULTS & VERIFICATION NUMBERS

> **Critical Presentation Rule**: Never mix up simulated results and real laptop numbers. Always present them with their clear, honest source labels.

### A. Simulated Environment Benchmark Results `[SIMULATED]`
- **Floor Dimensions**: $100\text{ m} \times 60\text{ m}$ ($6000\text{ m}^2$ total floor space)
- **Active Access Points**: 3 APs (Transmit Power $+20\text{ dBm}$)
- **Total Simulated Measurement Points**: 100+ points on regular grid
- **Dead Zones Detected (DBSCAN)**: **4 distinct dead zones**
  - *DZ-1 (Far Corner Office)*: Area $96\text{ m}^2$, Avg RSSI $-86.2\text{ dBm}$, Severity: **CRITICAL** (Factor: Distance $34\text{ m}$ + Wall loss $24\text{ dB}$)
  - *DZ-2 (Storage Wing)*: Area $84\text{ m}^2$, Avg RSSI $-82.1\text{ dBm}$, Severity: **HIGH** (Factor: Concrete partition loss $20\text{ dB}$)
  - *DZ-3 (East Corridor Nook)*: Area $64\text{ m}^2$, Avg RSSI $-79.5\text{ dBm}$, Severity: **MEDIUM**
  - *DZ-4 (Conference Annex)*: Area $48\text{ m}^2$, Avg RSSI $-78.8\text{ dBm}$, Severity: **LOW**
- **Total Dead-Zone Area Before Optimization**: **$292.0\text{ m}^2$**
- **Recommended Candidate Placements**: 2 APs added
- **Total Dead-Zone Area After Optimization**: **$68.0\text{ m}^2$**
- **Dead-Zone Area Reduction**: **$76.7\%$ reduction** ($224\text{ m}^2$ restored to healthy coverage)
- **ML Model Metrics (Random Forest)**:
  - Accuracy: **~89.3%**
  - Precision: **~88.5%**
  - Recall: **~86.2%**
  - F1-Score: **~87.3%**

### B. Live Hardware Laptop Verification `[REAL LAPTOP]`
*(Verified on student's actual physical machine)*
- **Connected SSID**: `Alifa’s iPhone` (Hotspot Wi-Fi test)
- **BSSID**: `a2:a4:e4:13:06:a7`
- **Radio Standard**: `802.11ax` (Wi-Fi 6)
- **Band & Channel**: $5\text{ GHz}$, Channel $149$
- **Signal Percentage**: $100\%$
- **Hardware RSSI**: $-29.0\text{ dBm}$ (`is_rssi_estimated: False`, reported directly by driver)
- **Physical Link Speed**: $1201.0\text{ Mbps}$ (Rx Rate)
- **Default Gateway IP**: `172.20.10.1` (automatically discovered via PowerShell `Get-NetRoute`)
- **Gateway Round-Trip Ping Latency**: $9.0\text{ ms}$ (Average of 3 ICMP echo requests)
- **Packet Loss**: $0.0\%$
- **Quality Score**: $98.5$ (**GOOD**)

---

## 13. HONEST ACADEMIC LIMITATIONS

When examiners ask *"What are the limitations of your project?"*, give this honest, mature answer. It shows deep academic maturity:

1. **User-Assisted Indoor Positioning**:
   GPS does not work reliably indoors due to satellite signal attenuation through roofs and concrete floors. True autonomous indoor positioning requires expensive Ultra-Wideband (UWB) anchors or Bluetooth Low Energy (BLE) beacon arrays. Our software uses **user-assisted positioning**: the user clicks their physical position on the digital map.
2. **2D Approximation vs 3D Multipath**:
   Our RF engine calculates wave propagation in a 2D floor plane. In real multi-story buildings, RF signals leak through ceilings/floors (inter-floor penetration) and bounce off metallic furniture (complex 3D multipath reflections).
3. **No Heavy Bandwidth Flooding**:
   To measure real throughput, tools like `iperf3` flood the network with maximum traffic, which would disrupt college classes or administrative work. Our system derives throughput from the physical modulation rate (link speed) or lightweight sampling rather than aggressive network saturation.
4. **Platform-Specific Wi-Fi Parsing**:
   The Real Survey telemetry collector uses native Windows tools (`netsh` and `powershell`). To run on macOS or Linux, equivalent shell adapters (`airport` or `iwconfig`/`nmcli`) would be needed.

---

## 14. 5-MINUTE PRESENTATION SCRIPT (INTEGRATED SPOKEN DEMO)

*(You can memorize this script or use it as a guideline during your major project viva presentation)*

> "Respected examiners, good morning.
>
> My major project is titled: **'AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System with OpenWrt-Based Student Authentication and Individual Data Quota Management'**.
>
> **The Problem:**
> In university campuses, engineering colleges, and hostels, network administrators face two major challenges:
> 1. Wi-Fi dead zones caused by thick concrete walls and long corridors make connectivity unreliable, but IT teams have no automated way to detect or predict them.
> 2. Campus internet bandwidth is often abused by unauthorized users or heavy downloaders because traditional captive portals lack individual USN validation, academic year parsing, and strict binary quota enforcement.
>
> **Our Integrated Solution:**
> We have built an end-to-end engineering system combining:
> - An **AI Wi-Fi Coverage & Dead-Zone Prediction Engine** that simulates and surveys indoor environments, uses **DBSCAN spatial clustering** to discover physical dead zones, trains a **Random Forest ML model** to predict weak spots in unmeasured rooms, and optimizes Access Point placements with verified Before-vs-After reduction metrics.
> - An **OpenWrt 25.12.5 and OpenNDS 10.3.1 Campus Gateway** that intercepts student devices, validates real college USNs (`ENG23CS0518`, `ENG23CT0112`), extracts admission batch years and departments, and enforces a strict daily binary quota of **$1\text{ GiB} = 1,024\text{ MiB}$** per student via kernel netfilter (`nds_mangle`).
>
> **How It Works (The 2 Core Modules):**
>
> **Module 1: AI Wi-Fi Optimization & ML Prediction**
> - In **Simulation Mode**, our COST-231 multi-wall RF engine models how $2.4\text{ GHz}$ and $5\text{ GHz}$ signals attenuate through concrete, drywall, and glass partitions across a $100\text{m} \times 60\text{m}$ floor.
> - In **Real College Survey Mode**, a student walks the corridors with a Windows laptop, clicks their location on the interactive floorplan, and samples live Wi-Fi signal (`netsh`) and wireless link latency (pinging the default gateway).
> - Degraded measurements are clustered using **DBSCAN**, discarding temporary outliers and drawing convex hull polygons around genuine dead zones.
> - Our **Random Forest model** achieves approximately **89% accuracy** in predicting dead-zone risk in unmeasured areas, and the AP optimizer recommends new coordinates that reduce dead-zone area by **over 75%**.
>
> **Module 2: OpenWrt Gateway & Student Quota Management**
> - The gateway runs on OpenWrt 25.12.5 inside VMware Workstation Pro, managing `br-lan` on `192.168.214.2` and internet uplinks on `eth0` and `eth2`.
> - **OpenNDS 10.3.1** intercepts HTTP traffic and implements **Secure FAS Level 1** redirection to our FastAPI backend at `192.168.214.1:8000/api/v1/gateway/portal`.
> - Real students self-register with their College USN. The backend validates format and batch year, placing new accounts into `PENDING_APPROVAL`. Access is **fail-closed**—zero internet until an administrator clicks **Approve** in the Gateway Console.
> - When authorized, the backend splits the daily $1,024\text{ MiB}$ quota into directional upload and download netfilter caps ($512\text{ MiB}$ upload + $512\text{ MiB}$ download), computes the SHA256 token $\text{tok} = \text{sha256}(\text{hid} + \text{faskey})$, and commands OpenNDS via SSH `ndsctl auth`.
>
> **Testing & Quality Assurance:**
> All **65 automated backend tests** pass cleanly with 100% pass rate, and the React 19 frontend compiles with zero errors.
>
> I am now ready to demonstrate both the AI Wi-Fi optimization pipeline and the OpenWrt student captive portal. Thank you."

---

## 15. 40 VIVA QUESTIONS & SIMPLE ANSWERS

### 📌 Conceptual & Networking Questions

**Q1: What is RSSI, and what unit is it measured in?**
**Answer:** RSSI stands for *Received Signal Strength Indicator*. It is measured in decibel-milliwatts ($\text{dBm}$). Because signal power drops dramatically over distance, it is represented on a logarithmic scale with negative numbers. For example, $-30\text{ dBm}$ is excellent, $-65\text{ dBm}$ is good, and $-85\text{ dBm}$ is very weak.

**Q2: What is a Wi-Fi dead zone according to your project?**
**Answer:** In our project, a dead zone is a continuous physical area where network performance degrades to an unusable level. It is defined multi-dimensionally: $RSSI < -78\text{ dBm}$, latency $> 120\text{ ms}$, packet loss $> 15\%$, or throughput $< 5\text{ Mbps}$.

**Q3: Why not just buy more Access Points and install them everywhere?**
**Answer:** Adding too many APs creates severe **Co-Channel Interference (CCI)**. When multiple APs transmit on the same frequency band, their radio waves collide, forcing devices to back off and wait, which actually decreases overall network speed. Intelligent placement eliminates dead zones with the minimum number of APs.

**Q4: What is the difference between $2.4\text{ GHz}$ and $5\text{ GHz}$ Wi-Fi?**
**Answer:** $2.4\text{ GHz}$ has a longer wavelength, so it penetrates walls better and covers larger distances, but offers lower maximum speed and suffers from channel congestion. $5\text{ GHz}$ provides much higher throughput and lower latency, but attenuates quickly through concrete walls and covers shorter distances.

**Q5: Why did you ping the local gateway instead of `8.8.8.8` during the survey?**
**Answer:** Pinging an external IP like `8.8.8.8` (Google DNS) measures internet traffic, ISP fiber delays, and cloud routing. Pinging the local gateway (the Wi-Fi router) isolates the **first-hop wireless radio link**, measuring purely the laptop's connection to the local AP.

---

### 📌 Machine Learning & Algorithm Questions

**Q6: What ML algorithm did you use for dead-zone prediction?**
**Answer:** We used a **Random Forest Classifier** with 100 decision trees (`n_estimators = 100`) and a maximum depth of 12.

**Q7: Why did you choose Random Forest instead of a Deep Learning Neural Network?**
**Answer:** Random Forest is ideal for tabular spatial-network features. Deep Neural Networks require tens of thousands of data samples, heavy GPU compute, and act as black boxes. Random Forest trains in seconds on a CPU, resists overfitting through ensemble bagging, and gives explicit **Feature Importance** rankings.

**Q8: What features does the ML model take as input?**
**Answer:** It takes 7 features: `rssi`, `latency`, `packet_loss`, `throughput`, `distance_to_ap`, `wall_factor`, and `ap_density` within a $25\text{m}$ radius.

**Q9: Explain Precision vs Recall in the context of Wi-Fi dead zones.**
**Answer:**
- **Precision** is: *"When the model predicts an area is a dead zone, is it really a dead zone?"* High precision prevents spending money installing APs where they aren't needed.
- **Recall** is: *"Out of all actual dead zones in the building, how many did the model find?"* High recall ensures no dead zone is overlooked.

**Q10: What is DBSCAN and why did you use it for dead-zone detection?**
**Answer:** DBSCAN is an unsupervised density-based spatial clustering algorithm. We used it because:
1. It does not require pre-specifying the number of clusters $K$.
2. It can find clusters of arbitrary geometric shapes (like hallways or L-shaped rooms).
3. It filters out isolated outliers as noise, ensuring a single bad measurement doesn't falsely trigger a dead zone.

**Q11: What do the DBSCAN parameters $\epsilon$ (epsilon) and $min\_samples$ represent?**
**Answer:** $\epsilon$ ($6$ to $12\text{ meters}$) is the maximum physical distance between two weak points for them to be considered neighbors. $min\_samples$ ($3$ points) is the minimum number of clustered poor points required to form a recognized dead zone.

**Q12: How do you calculate the area of a dead zone in square meters?**
**Answer:** We compute the 2D **Convex Hull** polygon encompassing the clustered points, and then calculate its surface area using the **Shoelace formula** on the polygon's Cartesian $(x, y)$ coordinates.

---

### 📌 RF Simulation & Physics Questions

**Q13: Which propagation model did you implement in the simulation?**
**Answer:** The **Multi-Wall COST-231 Indoor Propagation Model** (also aligned with ITU-R P.1238).

**Q14: How does your code calculate wall attenuation between an AP and a point?**
**Answer:** Using 2D computational geometry ray-intersection. The code draws a straight line segment from the AP coordinate to the receiver coordinate. It checks if this line intersects any wall line segment using cross products (`segments_intersect`). If an intersection occurs, the wall's attenuation in dB (e.g., $12\text{ dB}$ for concrete) is added to the total path loss.

**Q15: What is log-normal shadowing?**
**Answer:** In real environments, obstacles like desks, doors, and moving people cause random signal variations. Shadowing models this by adding a zero-mean Gaussian random variable $X_\sigma \sim \mathcal{N}(0, \sigma^2)$ (with $\sigma = 1.8\text{ dB}$) to the path loss equation.

---

### 📌 System Architecture & Real Survey Questions

**Q16: How does the laptop know where it is inside the building?**
**Answer:** It does not use automatic indoor GPS because GPS signals cannot penetrate building roofs. Instead, the user marks their current physical position on the digital interactive floorplan by clicking the screen, which sets the $(x, y)$ coordinates.

**Q17: How did you extract Wi-Fi details from Windows without extra software?**
**Answer:** By running the native Windows Command Prompt command: `netsh wlan show interfaces` using Python's `subprocess.run()`, and parsing fields like SSID, BSSID, Signal %, and Channel with regular expressions (`re`).

**Q18: What is BSSID and why is it important?**
**Answer:** BSSID is the Basic Service Set Identifier, which is the hardware MAC address of the specific Access Point radio your laptop is connected to. In a campus with 50 APs all sharing the same SSID (e.g., `Campus_WiFi`), the BSSID tells us *exactly* which physical AP the device is communicating with.

**Q19: If Windows only reports Signal percentage (e.g., 75%), how do you get RSSI in dBm?**
**Answer:** If the Wi-Fi driver does not expose raw RSSI, we apply the standard Microsoft WLAN approximation formula:
$$\text{RSSI (dBm)} \approx \left(\frac{\text{Signal \%}}{2}\right) - 100$$
For example, $80\% \rightarrow (40) - 100 = -60\text{ dBm}$. Our database clearly tags whether RSSI was hardware-reported or estimated.

**Q20: Why did you use FastAPI instead of Flask or Django?**
**Answer:** FastAPI provides native asynchronous request handling, automatic OpenAPI/Swagger interactive documentation (`/docs`), and strict data validation using Pydantic models. It is significantly faster and more modern than Flask.

**Q21: Why SQLite instead of MongoDB or PostgreSQL?**
**Answer:** SQLite is embedded, serverless, and stores data in a single local file. Since our project is designed to run locally on a student's survey laptop while walking around campus, SQLite eliminates the need to run heavy background database services.

---

### 📌 AP Optimization & Verification Questions

**Q22: How does the optimizer pick candidate locations for new APs?**
**Answer:** It generates candidates primarily at the **centroids** of detected dead-zone polygons and affected room centers, enforcing a minimum separation constraint ($12\text{ meters}$) from existing APs to prevent co-channel overlap.

**Q23: How do you verify that the AP recommendation actually worked?**
**Answer:** The system runs a **Before vs After** evaluation. It re-computes the spatial coverage with the new AP in place, measures the new dead-zone area in $m^2$, and calculates the percentage area reduction (typically achieving $>75\%$ reduction).

**Q24: What are the severity levels of dead zones in your system?**
**Answer:** LOW, MEDIUM, HIGH, and CRITICAL, calculated via a multi-parameter composite penalty score based on RSSI, latency, packet loss, and throughput.

**Q25: Can this system be deployed in our college right now?**
**Answer:** Yes. A network administrator or student can open the Real College Survey mode on their laptop, upload our floorplan, walk the corridors, click their spots, and capture real measurements to detect dead zones immediately.

**Q26: What happens if the laptop disconnects from Wi-Fi during the survey?**
**Answer:** The backend detects `State: disconnected` in the `netsh` output. It records `connected: False`, sets packet loss to $100\%$, and marks the quality as `POOR` with zero latency, accurately representing a total dead zone.

**Q27: How many tests did you write, and what do they test?**
**Answer:** We wrote 65 automated tests using Pytest across 9 test files, covering API endpoints, RF path loss physics, DBSCAN clustering, Random Forest training/inference, AP optimization logic, Windows network telemetry, USN validation, student approval workflows, and OpenNDS FAS Level 1 authentication.

**Q28: Is this a software-only project or does it need hardware sensors?**
**Answer:** It is strictly **software-only**. It uses the built-in Wi-Fi radio and networking stack already present inside a standard Windows laptop. No Arduinos, Raspberry Pis, or external antennas are required.

**Q29: What is the main difference between your project and commercial tools like NetSpot or Ekahau?**
**Answer:** NetSpot and Ekahau primarily create passive heatmaps of signal strength. Our project is an end-to-end AI system: it clusters multi-parameter weak spots with DBSCAN, diagnoses root causes, uses Machine Learning to predict dead zones in unmeasured locations, and automatically suggests AP coordinates with verified before/after reduction metrics.

**Q30: What future enhancements would you suggest?**
**Answer:** Extending the RF model to 3D for multi-floor buildings (inter-floor RF penetration), adding automated Wi-Fi channel allocation algorithms (to prevent channel overlap), and developing a cross-platform mobile client for Android/iOS.

---

### 📌 OpenWrt, Captive Gateway & Quota Management Questions

**Q31: What router operating system are you using and where does it run?**
**Answer:** We run **OpenWrt 25.12.5 (x86_64)** as a virtual machine inside VMware Workstation Pro. It acts as our college campus gateway router.

**Q32: What is OpenNDS, and what version is installed?**
**Answer:** OpenNDS is a lightweight, high-performance captive portal daemon for OpenWrt that integrates directly with Linux kernel netfilter (`nds_mangle`). We run **OpenNDS 10.3.1**.

**Q33: What is Forwarding Authentication Service (FAS) Level 1?**
**Answer:** FAS Level 1 is a secure captive portal architecture where OpenNDS intercepts the client's HTTP browser request and redirects it to an external portal (our FastAPI backend). The backend authenticates the student and signs the redirect using a SHA256 cryptographic token: $\text{tok} = \text{SHA256}(\text{hid} + \text{faskey})$. The gateway validates the token before unlocking internet access.

**Q34: How does the backend communicate with OpenWrt to authorize a student?**
**Answer:** The FastAPI backend uses **Paramiko** over an **ed25519 SSH key pair** to execute authoritative OpenNDS control commands non-interactively:
```bash
ndsctl auth <client_mac> <session_timeout_mins> <upload_quota_kb> <download_quota_kb>
```

**Q35: What is your quota standard and why is it 1,024 MiB instead of 1,000 MB?**
**Answer:** We strictly follow the **Binary IEC standard** ($1\text{ GiB} = 1,024\text{ MiB} = 1,048,576\text{ KiB}$). Network packet counters, operating system buffers, and OpenNDS netfilter operate on binary powers of 2 ($2^{10} = 1,024$). Using decimal SI ($1,000\text{ MB}$) creates discrepancies between router counters and database records.

**Q36: Why do you divide the student's quota into upload and download caps?**
**Answer:** OpenNDS takes separate upload and download quota limits in `ndsctl auth`. If a student has $1,024\text{ MiB}$ remaining and we assign $1,024\text{ MiB}$ to upload and $1,024\text{ MiB}$ to download, the student could consume up to $2,048\text{ MiB}$ ($2\text{ GiB}$) in total! Dividing the quota evenly ($512\text{ MiB}$ up + $512\text{ MiB}$ down) strictly guarantees the total combined transfer cannot exceed the assigned $1,024\text{ MiB}$ limit.

**Q37: What is the student USN validation format?**
**Answer:** It uses the regex `^[A-Za-z]{3}\d{2}[A-Za-z]{2}\d{3,5}$`.
For example, `ENG23CS0518` represents Institution `ENG`, Admission Batch `2023`, Department `CS` (Computer Science & Engineering), and Roll Number `0518`. In 2026, the calculated academic year is **4th Year / Final Year**.

**Q38: What is your fail-closed security policy?**
**Answer:** If the OpenWrt gateway is unreachable, if the student account is `PENDING_APPROVAL`, `REJECTED`, or `DISABLED`, or if the quota is exhausted ($\le 0\text{ MiB}$), the system returns HTTP 403 Forbidden and **never authorizes the device**. Security events and login attempts are immutably recorded in the gateway audit ledger.

**Q39: Why does a real smartphone need a physical AP or USB Wi-Fi adapter to test the captive portal?**
**Answer:** The laptop's internal Wi-Fi card is a receiver connected to an uplink hotspot (WAN2 `eth2`). VMware's `br-lan` interface is virtual (`VMnet1`). Virtual switches cannot transmit radio waves over the air. To connect a physical smartphone, either an external physical Wi-Fi AP must be bridged to `br-lan` via the Ethernet port, or a USB Wi-Fi dongle must be connected directly to the OpenWrt VM.

**Q40: Can a student bypass their quota by changing their IP address?**
**Answer:** No. OpenNDS binds the student's session to their verified hardware **MAC address** and kernel netfilter connection tracking (`conntrack`). Changing the IP address causes netfilter to drop packets or re-intercept the device because the IP no longer matches the authenticated MAC-IP pair.

---

## 16. QUICK CHEAT SHEET (5-MINUTE REVISION)

```
================================================================================
                    ⚡ 5-MINUTE LAST-MINUTE VIVA CHEAT SHEET ⚡
================================================================================

1. PROJECT IN ONE SENTENCE:
   An integrated platform that combines AI spatial Wi-Fi analysis (DBSCAN dead-zone
   clustering, Random Forest prediction, AP optimization) with an OpenWrt 25.12.5 /
   OpenNDS 10.3.1 student gateway enforcing USN validation and 1 GiB daily quotas.

2. THE TWO MAJOR MODULES:
   • Module 1: AI Wi-Fi Coverage Optimization (DETECT ➔ UNDERSTAND ➔ PREDICT ➔ OPTIMIZE ➔ VERIFY)
   • Module 2: OpenWrt Campus Student Gateway (USN Parsing, FAS Level 1, 1 GiB Quota, Netfilter)

3. KEY THRESHOLDS & MATHEMATICAL CONSTANTS:
   • Poor Signal (RSSI):   < -78 dBm
   • High Latency:         > 120 ms
   • High Packet Loss:     > 15%
   • Low Throughput:       < 5 Mbps
   • Binary Quota Standard: 1 GiB = 1,024 MiB = 1,048,576 KiB
   • Directional Quota Split: 512 MiB Upload / 512 MiB Download (prevents double allocation)
   • FAS Level 1 Token:    tok = SHA256(hid + faskey)

4. CORE NETWORKING & TOPOLOGY DETAILS:
   • Router Gateway IP:    192.168.214.2 (OpenWrt br-lan on VMnet1)
   • Backend Portal URL:   http://192.168.214.1:8000/api/v1/gateway/portal
   • OpenNDS Daemon Port:  2050 (MHD server on OpenWrt)
   • SSH Management:       Ed25519 key (root@192.168.214.2)
   • Trusted MAC:          00:50:56:C0:00:01 (Host VMnet1 - preserves LuCI & SSH)

5. USN PARSING RULES (e.g., ENG23CS0518):
   • Prefix: ENG (College) | Year: 23 -> 2023 Batch | Dept: CS (Comp Science) | Roll: 0518
   • Academic Year in 2026: 4th Year / Final Year (2026 - 2023 = 3)
   • Initial Registration: PENDING_APPROVAL (Fail-closed: zero internet until admin approves)

6. BENCHMARK NUMBERS:
   • Automated Tests:      65 / 65 Passed (100% Pass Rate via Pytest)
   • Frontend Build:       React 19 / TypeScript ✓ Built in 694ms (0 errors)
   • ML Accuracy:          ~89% (Random Forest, 100 Trees)
   • AP Optimization:      >75% dead-zone area reduction (e.g., 292 m² -> 68 m²)
   • Live Hardware Test:   Alifa’s iPhone, BSSID a2:a4:e4:13:06:a7, 100%, 9ms latency

7. FOUR COMMON TRAP QUESTIONS:
   • "Why DBSCAN?"         -> Discovers cluster count automatically; ignores single-point noise.
   • "Why Ping Gateway?"   -> Isolates the wireless Wi-Fi link from external ISP internet lag.
   • "Why Split Quota?"    -> OpenNDS sets separate up/down caps; splitting avoids doubling quota.
================================================================================
```

---

## 17. STEP-BY-STEP WINDOWS STARTUP, TESTING & VIVA GUIDE

### 17.1 How to Start the Application on Windows

Open **Windows PowerShell** (or Windows Terminal) and run:

#### Terminal 1 — Start FastAPI Backend:
```powershell
cd c:\Users\alifa\OneDrive\Documents\Major_Project_Implementation
.\venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
*Expected Output:*
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

#### Terminal 2 — Start React Vite Frontend:
```powershell
cd c:\Users\alifa\OneDrive\Documents\Major_Project_Implementation\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
*Expected Output:*
```
  VITE v8.3.2  ready in 480 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: use --host to expose
```

---

### 17.2 Complete System URLs

| Service | Access URL | Credentials |
|---|---|---|
| **Welcome Landing Screen** | `http://localhost:5173` | Direct browser access |
| **Student Wi-Fi Portal** | `http://localhost:5173` (Student Login) | Demo accounts or registered USN |
| **Campus Admin Portal** | `http://localhost:5173` (Admin Portal) | `admin` / `[REDACTED_ADMIN_PASSWORD]` |
| **Interactive API Documentation** | `http://127.0.0.1:8000/docs` | Swagger UI with testable endpoints |
| **OpenNDS Gateway Engine** | `http://192.168.214.2:2050` | OpenNDS MHD daemon on OpenWrt |
| **OpenWrt LuCI Web GUI** | `http://192.168.214.2:8080` | `root` (No password configured) |

---

### 17.3 How to Run the Automated Verification Suite

Run all 65 automated tests directly from PowerShell:
```powershell
cd c:\Users\alifa\OneDrive\Documents\Major_Project_Implementation
.\venv\Scripts\python -m pytest backend\tests -v
```

To run the live student registration and approval integration test:
```powershell
.\venv\Scripts\python scripts/verify_workflow.py
```

---

### 17.4 Step-by-Step Viva Demonstration Walkthrough

When presenting to the external examiner, follow these 5 clear steps:

1. **Step 1: Open Welcome Screen (`http://localhost:5173`)**
   - Say: *"Our application separates roles cleanly: students authenticate through a captive portal, while administrators manage quotas and AI coverage optimization."*
   - Point out the 3 large action cards: Student Wi-Fi Login, Student Registration, and Admin Portal.
   - Point out the live OpenWrt gateway indicator (`192.168.214.2: ONLINE`).

2. **Step 2: Demonstrate Student Registration & USN Validation**
   - Click **Student Registration**.
   - Type in `ENG23CS0518` and name `Rahul Sharma`.
   - Point out the live badge showing `Computer Science Core`, `Batch 2023`, and `4th Year / Final Year`.
   - Click **Submit Registration for Approval**.
   - Show the examiner that the account enters `PENDING_APPROVAL` status and cannot access the internet yet (fail-closed security).

3. **Step 3: Demonstrate Admin Review & Approval**
   - Click **Admin Portal** $\rightarrow$ log in with `admin` and `[REDACTED_ADMIN_PASSWORD]`.
   - Open **Student Gateway & Quotas**.
   - Show the examiner the **Pending Registrations** alert table showing `ENG23CS0518`.
   - Click **Approve**. The account immediately switches to `APPROVED` and `ACTIVE`.
   - Explain the binary IEC daily quota ($1\text{ GiB} = 1,024\text{ MiB}$) and directional netfilter split.

4. **Step 4: Demonstrate Student Wi-Fi Login & Quota Countdown**
   - Click **Exit Admin** $\rightarrow$ click **Student Wi-Fi Login**.
   - Click the pre-configured demo card for `DEMO-USN-CSE01` (Aditya Sharma).
   - Click **Connect Device to Campus Internet**.
   - Show the active session confirmation, remaining quota ($1,024.0\text{ MiB}$), upload allowance ($153.6\text{ MiB}$), and download allowance ($870.4\text{ MiB}$).
   - Click `DEMO-USN-EXH05` $\rightarrow$ show that exhausted accounts are strictly denied internet access (HTTP 403).

5. **Step 5: Demonstrate AI Wi-Fi Optimization**
   - Open **Admin Portal** $\rightarrow$ **Dashboard**.
   - Click **Generate Demo Environment** $\rightarrow$ select `Laboratory Dead Zone`.
   - Show the 5 key AI stages:
     - **Dead-Zone Analysis**: DBSCAN clusters weak points into named polygon dead zones ($m^2$ area).
     - **Coverage Map**: Color-coded signal heatmap showing wall penetration drop-offs.
     - **Dead-Zone Prediction**: Random Forest ML model extrapolates risk across unmeasured coordinates.
     - **AP Optimization**: System calculates centroid placements for new APs.
     - **Before vs After**: Dual-simulation verifies $>75\%$ reduction in dead-zone area.

---

### 17.5 Troubleshooting Common Issues

| Issue | Cause | Solution |
|---|---|---|
| **Port 8000 in use** | A previous Python/uvicorn process is still running | In PowerShell: `Get-Process python \| Stop-Process -Force`, then restart uvicorn |
| **Port 5173 in use** | A previous Vite dev server is running | In PowerShell: `npx kill-port 5173`, then re-run `npm run dev` |
| **OpenWrt Gateway Offline** | VMware virtual machine is paused or suspended | Open VMware Workstation, resume the `OpenWrt` VM, and verify IP `192.168.214.2` |
| **Student Login shows 502** | No physical smartphone connected on `br-lan` | Ensure the **Viva / Browser Evaluation Mode** toggle is switched **ON** in the login form |
