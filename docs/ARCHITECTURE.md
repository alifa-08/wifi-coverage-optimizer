# System Architecture

## 1. Executive Summary

The **AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System** is a software-based platform designed for educational, administrative, and enterprise campus environments. The primary technical novelty is **AI-BASED WI-FI DEAD-ZONE DETECTION AND DEAD-ZONE PREDICTION**, structured along a rigorous five-stage pipeline:

```
DETECT ➔ UNDERSTAND ➔ PREDICT ➔ OPTIMIZE ➔ VERIFY
```

The system operates entirely on a standard PC or Windows laptop without requiring physical routers, external sensors, microcontroller hardware (ESP32/Arduino), or paid cloud APIs.

---

## 2. Component Architecture

```
+-------------------------------------------------------------------------------+
|                             FRONTEND CLIENT                                  |
|         React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons           |
|                                                                               |
|  [Dashboard]          [Dead-Zone Analysis]   [Coverage Map (SVG Floorplan)]   |
|  [ML Prediction Map]  [AP Optimization]      [Before vs After Verification]   |
|  [Network Analytics]  [Alerts & Remediation] [Simulation Studio & CSV Import] |
+---------------------------------------+---------------------------------------+
                                        | REST API (HTTP/JSON)
                                        v
+-------------------------------------------------------------------------------+
|                            FASTAPI BACKEND SERVICE                            |
|                                                                               |
|  +--------------------+  +--------------------+  +-------------------------+  |
|  |  Simulation Engine |  |  Dead-Zone Engine  |  |   ML Prediction Engine  |  |
|  | - Cost-231 PathLoss|  | - DBSCAN Cluster   |  | - Random Forest (100 tr)|  |
|  | - Multi-Wall Ray   |  | - Convex Hull (m²) |  | - Stratified Split     |  |
|  | - Shadowing Noise  |  | - Multi-Param Rank |  | - Grid Inference (P_dz)|  |
|  +--------------------+  +--------------------+  +-------------------------+  |
|                                                                               |
|  +--------------------------------------------+  +-------------------------+  |
|  |        AP Placement Optimizer              |  |   Alerts & Persistence  |  |
|  | - Candidate Grid Generation                |  | - Cross-Run Observation |  |
|  | - Area & Count Reduction Delta             |  | - Incident Resolution   |  |
|  | - Before vs After Verification             |  | - CSV Survey Ingestion  |  |
|  +--------------------------------------------+  +-------------------------+  |
+---------------------------------------+---------------------------------------+
                                        | SQLAlchemy ORM
                                        v
+-------------------------------------------------------------------------------+
|                            SQLITE LOCAL DATABASE                              |
|   buildings, floors, rooms, walls, access_points, measurements, dead_zones,  |
|   dead_zone_observations, prediction_grid_points, ml_model_metadata, alerts   |
+-------------------------------------------------------------------------------+
```

---

## 3. Physical RF Simulation Model

To eliminate hardware dependencies while upholding scientific validity, signal propagation is simulated using the **Multi-Wall Cost-231 / ITU-R P.1238 Indoor Model**:

$$PL(d) = PL(d_0) + 10 \cdot n \cdot \log_{10}\left(\frac{d}{d_0}\right) + \sum_{w=1}^{W} L_{w}$$

Where:
- $d_0 = 1.0\text{ m}$: Reference distance.
- $PL(d_0) = 40.0\text{ dB}$: Free space loss at 1 meter for 2.4 GHz frequency.
- $n = 3.0$: Indoor multi-partition path loss exponent.
- $\sum L_w$: Cumulative attenuation of structural walls intersected by ray-tracing from access point to receiver.
  - Reinforced Concrete partition: $14.0\text{ dB}$ to $16.0\text{ dB}$ attenuation.
  - Brick divider: $9.0\text{ dB}$ to $10.0\text{ dB}$ attenuation.
  - Glass / drywall: $3.0\text{ dB}$ to $5.0\text{ dB}$ attenuation.

Received Signal Strength Indicator (RSSI) is computed as:

$$\text{RSSI} = P_{tx} - PL(d) + \mathcal{N}(0, \sigma^2)$$

Where $P_{tx} = 20.0\text{ dBm}$ (100 mW) and $\mathcal{N}(0, \sigma^2)$ models log-normal shadowing and multi-path fading ($\sigma = 1.8\text{ dB}$).

Network performance metrics (Latency, Packet Loss, Throughput) are logically derived from received power:
- **Good Signal ($\text{RSSI} \ge -65\text{ dBm}$)**: Latency $10\text{--}25\text{ ms}$, Loss $0.1\text{--}1.0\%$, Throughput $150\text{--}250\text{ Mbps}$.
- **Moderate Signal ($-78 \le \text{RSSI} < -65\text{ dBm}$)**: Latency $30\text{--}75\text{ ms}$, Loss $1.5\text{--}6.0\%$, Throughput $30\text{--}110\text{ Mbps}$.
- **Poor / Dead Zone ($\text{RSSI} < -78\text{ dBm}$)**: Latency $130\text{--}450\text{ ms}$, Loss $15\text{--}65\%$, Throughput $0.2\text{--}6.0\text{ Mbps}$.
