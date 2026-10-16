# User Guide & Viva Demonstration Manual

## 1. Quickstart

To launch the complete application on a Windows machine:

1. Double-click **`scripts/run_all.bat`** (or execute in PowerShell).
   - Backend API starts on: `http://localhost:8000`
   - Frontend Dashboard starts on: `http://localhost:5173`
   - Automatic Swagger API docs: `http://localhost:8000/docs`

---

## 2. Project Viva Demonstration Flow

Follow this exact walkthrough during project presentation or evaluation:

1. **Launch Environment**:
   - Open browser to `http://localhost:5173`.
   - In the top navigation bar, ensure the scenario is set to **"Laboratory Dead Zone"**.
   - Click the prominent **"Generate Demo Environment"** button.
   - The system automatically creates the campus floorplan, simulates 1,000 measurements, clusters dead zones, trains the ML model, predicts risk grids, and calculates AP recommendations.

2. **Step 1: Dashboard Inspection**:
   - Observe the 4 Core Inquiry cards:
     - *Where are the dead zones?* (Shows count and area in $m^2$).
     - *Why are they occurring?* (Identifies concrete partition attenuation).
     - *Where could new dead zones occur?* (ML-predicted points).
     - *How can we reduce them?* (Calculated AP recommendations).
   - Review KPI cards: Current Dead Zones, Dead-Zone Area ($m^2$), Coverage Score, Average RSSI, Latency, and Packet Loss.

3. **Step 2: Dead-Zone Analysis**:
   - Navigate to **"Dead-Zone Analysis"** via the sidebar.
   - Click on **"DZ-1: Software Systems Lab 1"** or **"DZ-2: Seminar Hall 103"**.
   - Review the **Root-Cause Diagnostics** box explaining wall attenuation ($15\text{--}30\text{ dB}$) and physical distance.
   - Observe the **Persistence Score** tracking recurring dead zones across runs.

4. **Step 3: Coverage Map**:
   - Navigate to **"Coverage Map"**.
   - Toggle layers on and off (Rooms, Walls, AP propagation halos, Measurement dots, Dead-Zone Polygons, ML Predicted Risk).
   - Hover over points and dead zones to see live telemetry inspection tooltips.

5. **Step 4: AI Dead-Zone Prediction**:
   - Navigate to **"Dead-Zone Prediction"**.
   - Adjust the **Confidence / Probability Threshold slider** (e.g. 50% to 75%).
   - Observe the distinct comparison between **Measured Dead Zones** and **ML-Predicted Potential Dead Zones**.
   - Inspect the table of unmeasured high-risk coordinates.

6. **Step 5: AP Optimization**:
   - Navigate to **"AP Optimization"**.
   - Review recommended AP coordinates and their expected recoverable area in $m^2$.
   - Click **"Run Before vs After Verification"**.

7. **Step 6: Before vs After Verification**:
   - Observe the quantitative Dead-Zone Area Reduction (typically $60\%\text{--}80\%$ drop).
   - Toggle between **BEFORE**, **AFTER**, and **SIDE-BY-SIDE** floorplans to see the dead zones vanish!

8. **Step 7: Alerts Resolution**:
   - Navigate to **"Alerts"**.
   - View active critical dead-zone alerts and click **"Resolve Incident"**.

9. **Step 8: Machine Learning Inspector**:
   - Navigate to **"ML Model Inspector"**.
   - Show the authentic test set metrics: Accuracy ($>80\%$), Precision, Recall, and F1-Score.
   - Review the 2x2 Confusion Matrix and Feature Importance ranking.
   - Click **"Retrain Model On-Demand"** to demonstrate live training.

---

## 3. CSV Survey Data Ingestion

To ingest walk-test survey measurements:
1. Navigate to **"Simulation & CSV"**.
2. Click **"Download Template"** to review expected CSV headers:
   `timestamp, floor, x, y, rssi, latency, packet_loss, throughput, ap_id`
3. Select your CSV file and click **"Upload & Detect Dead Zones"**.
4. The system ingests all points and executes the DBSCAN clustering algorithm immediately.
