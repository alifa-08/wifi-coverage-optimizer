# Real College Survey Mode — Field Operation & Viva Guide

## 1. Executive Summary & Purpose

The **Real College Survey Mode** enables taking a standard Windows laptop into a college building (e.g., Academic Block, Library, Hostels, Laboratories) and capturing authentic physical Wi-Fi and network health measurements.

Unlike synthetic simulations or commercial RF surveying kits that demand specialized spectrum analyzers, Raspberry Pis, or ESP32 hardware, this system leverages **built-in Windows operating system commands (`netsh wlan show interfaces`) and ICMP echo telemetry**.

All captured measurements are stored with an explicit academic provenance flag (`is_synthetic = false`) and directly plug into the existing AI dead-zone detection and prediction engine:
$$\text{SURVEY} \rightarrow \text{DETECT} \rightarrow \text{UNDERSTAND} \rightarrow \text{PREDICT} \rightarrow \text{OPTIMIZE} \rightarrow \text{VERIFY}$$

---

## 2. Technical Architecture & Windows Telemetry Extraction

### 2.1 What Local Windows Commands Expose
The backend surveyor (`backend/app/survey/collector.py`) executes native OS utilities with strict non-blocking timeouts:

| Telemetry Metric | Extraction Source | Fallback / Conversion | Academic Provenance |
|---|---|---|---|
| **SSID** | `netsh wlan show interfaces` | None | Direct hardware report |
| **BSSID (MAC)** | `netsh wlan show interfaces` | `N/A` if not reported | Physical AP hardware address |
| **Radio Type** | `netsh wlan show interfaces` | `802.11` | Standard (802.11ac / 802.11ax / 802.11n) |
| **Channel & Band** | `netsh wlan show interfaces` | Band inferred (2.4 GHz vs 5 GHz) | Direct hardware report |
| **Link Speed** | `netsh wlan show interfaces` | Max(Tx, Rx) in Mbps | Physical link data rate |
| **Signal Quality** | `netsh wlan show interfaces` | Reported as Percentage `0–100%` | Native Windows Driver metric |
| **RSSI (dBm)** | Hardware `Rssi` if available | Approximated via Microsoft standard formula | Explicitly flagged `is_rssi_estimated: true/false` |
| **Link Latency** | `ping -n 3 -w 1000 <Target>` | Round-trip time in milliseconds | Local gateway (isolates Wi-Fi link) |
| **Packet Loss** | `ping -n 3 -w 1000 <Target>` | Percentage loss `0–100%` | ICMP loss |

### 2.2 Academic Honesty Regarding Signal Strength (Percentage vs dBm)
Windows 10/11 WLAN network drivers return signal strength as a percentage:
$$\text{Signal } \in [0\%, 100\%]$$
Certain high-end Intel or Realtek drivers also expose a true hardware `Rssi` field (e.g., `-58 dBm`).

Where hardware RSSI is omitted by the manufacturer's driver, the system derives an approximate RSSI using the standard Microsoft NDIS formula:
$$\text{RSSI}_{\text{estimated}} = \left(\frac{\text{Signal}_{\%}}{2}\right) - 100 \quad [\text{dBm}]$$

*Viva Defense Note*: The system **never fabricates** raw RF data. In every CSV export, database record, and UI card, `is_rssi_estimated` is explicitly logged, ensuring full scientific rigor.

### 2.3 Isolating Wi-Fi Link Latency via the Default Gateway
Pinging an external internet IP (e.g., `8.8.8.8`) introduces variables from college ISP bandwidth throttling and WAN saturation. To measure the **pure wireless link latency**, our system dynamically resolves the college network's local Default Gateway address:
```powershell
Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -ExpandProperty NextHop
```
(e.g., `172.20.10.1` or `192.168.1.1`). Pinging the gateway measures only the laptop $\leftrightarrow$ Access Point $\leftrightarrow$ Switch path.

---

## 3. Step-by-Step Practical Surveying Walkthrough

### Preparation Before Entering the Building
1. Start the application on your laptop:
   ```powershell
   # Terminal 1: Backend
   cd backend
   ..\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```
2. Open your browser at `http://localhost:5173`.
3. Connect your laptop's Wi-Fi to the target campus network (e.g. `College-Campus-WiFi`).
4. Select the **Real College Survey** tab on the navigation sidebar.

### In-Building Survey Procedure
1. **Select Floor**: Choose the digital floorplan corresponding to the level you are walking (e.g., *Academic Block - Floor 1*).
2. **Start or Pick a Session**:
   - Click the `+` button to create a new session (e.g., *"Library 2nd Floor Survey"*).
3. **Walk to a Physical Spot**:
   - Walk to a physical location (e.g., front desk, central corridor, corner laboratory).
4. **Pin Your Position**:
   - On the digital floorplan canvas, click or tap where you are standing. An animated indigo Target Pin appears showing your coordinates $(X, Y)$ in calibrated meters.
   - *(Optional)* Type a descriptive note (e.g., *"Behind concrete pillar in Lab 101"*).
5. **Capture Measurement**:
   - Click the prominent **Capture Measurement at Pin** button.
   - The backend synchronously polls `netsh wlan` and executes the gateway ping.
   - The measurement appears instantly as a color-coded node:
     - 🟢 **Green** (`GOOD`): Signal $\ge 70\%$, RSSI $\ge -65\text{ dBm}$, latency $\le 50\text{ ms}$, loss $\le 2\%$.
     - 🟡 **Amber** (`MODERATE`): Signal $40-69\%$, RSSI $-66\text{ to }-78\text{ dBm}$, latency $\le 120\text{ ms}$.
     - 🔴 **Red** (`POOR`): Signal $< 40\%$, RSSI $< -78\text{ dBm}$, latency $> 120\text{ ms}$, or packet loss $\ge 15\%$.
6. **Repeat Across Multiple Locations**:
   - Walk to 6 to 15 different locations across the floor to ensure sufficient spatial density.
   - The UI includes an automatic density monitor: if fewer than 4 points are captured, a warning banner reminds you to collect more sample locations for spatial clustering.

---

## 4. Running AI Dead-Zone Detection on the Survey Dataset

Once survey locations are collected, click **Run Dead-Zone Detection**:

1. **Bridge to Detection Engine**:
   - The system aggregates the real survey measurements into an evaluation run tagged with `is_synthetic = false`.
2. **DBSCAN Spatial Clustering**:
   - Poor-quality points are clustered based on Euclidean physical distance $\epsilon = 12.0\text{ m}$.
3. **Polygon & Bounding Box Generation**:
   - Bounding boxes and convex hulls are computed around clusters.
4. **Multi-Factor RF Diagnosis**:
   - Contributing factors are diagnosed (e.g., *Extremely Weak RF Signal*, *Excessive Latency Spike*, *High Packet Loss*).
5. **Interactive Visualization**:
   - Detected real dead zones appear on the floorplan with red hatched textures and severity badges.
   - Clicking any dead zone navigates directly to the comprehensive **Dead-Zone Analysis** breakdown.

---

## 5. Exporting Survey Data & Viva Voce Q&A

### 5.1 Exporting to CSV
At any point, click **Export Session CSV** to download a standards-compliant CSV file containing:
```csv
timestamp,floor_id,x,y,ssid,bssid,signal_percent,rssi_dbm,is_rssi_estimated,channel,band,radio_type,link_speed_mbps,latency_ms,packet_loss_percent,ping_target,quality_score,quality_category,is_synthetic
2026-10-04T10:00:00,1,12.5,10.0,College_Campus_WiFi,00:1a:2b:3c:4d:5e,92,-54.0,false,36,5 GHz,802.11ax,866.0,14.0,0.0,172.20.10.1,90.0,GOOD,false
```
You can also click **Sample CSV Template** to review a reference 15-point real-world walk survey dataset.

### 5.2 Anticipated Viva Voce Questions & Answers

**Q1: How does your laptop know where it is inside the building?**
> *"Our project intentionally avoids claiming automatic indoor GPS or trilateration because standard laptop Wi-Fi chips cannot accurately localize indoors without dense beacon infrastructure. Instead, our system utilizes a user-assisted digital floorplan pinning approach: the user marks their known physical location on the calibrated floorplan and triggers an instant capture of authentic Windows adapter telemetry."*

**Q2: What is the difference between Simulation Mode and Real Survey Mode?**
> *"In Simulation Mode, RF propagation is modeled via the Multi-Wall Path Loss (COST231) model with wall attenuation factors and log-distance shadowing. In Real Survey Mode, all measurements originate directly from the laptop's Windows WLAN driver via `netsh wlan show interfaces` and local gateway ping tests. Both modes seamlessly feed into the same AI dead-zone detection and Random Forest prediction pipeline."*

**Q3: How do you handle signal percentage versus dBm?**
> *"Windows native APIs report signal quality as a percentage (0-100%). When the network adapter driver provides true hardware RSSI, we record that directly (`is_rssi_estimated = false`). When the driver omits it, we derive RSSI using Microsoft's standard formula `(Signal% / 2) - 100` and explicitly tag the record with `is_rssi_estimated = true`. We never falsify or fabricate RF data."*

**Q4: Why ping the default gateway instead of Google (8.8.8.8)?**
> *"Pinging the local default gateway isolates the wireless link quality (laptop to access point to local router) from external internet congestion, ISP throttling, or campus firewall delays. This ensures our latency and packet loss metrics directly reflect Wi-Fi health."*
