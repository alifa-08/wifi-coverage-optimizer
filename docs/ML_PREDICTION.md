# Machine Learning: Dead-Zone Prediction

## 1. Objective

The primary AI objective is **extrapolating dead-zone risk to unmeasured physical locations**. Administrators cannot manually survey every square foot of an academic or corporate facility. By learning the non-linear interaction between structural architecture, physical distance, and network telemetry, the trained classifier predicts whether an unmeasured point $(x, y)$ constitutes a potential dead zone.

---

## 2. Feature Engineering

Features used for training and spatial inference:

| Feature Name | Type | Description |
|---|---|---|
| `rssi` | Float (dBm) | Estimated or measured received signal strength indicator |
| `latency` | Float (ms) | Round-trip transmission time |
| `packet_loss` | Float (%) | Dropped packet ratio |
| `throughput` | Float (Mbps) | Available data transmission rate |
| `distance_to_ap` | Float (m) | Euclidean distance to closest active access point |
| `wall_factor` | Float (dB) | Cumulative wall attenuation along direct sight line |
| `ap_density` | Integer | Count of functional APs within 25-meter radius |

---

## 3. Classification Algorithm & Pipeline

- **Algorithm**: `RandomForestClassifier` (100 Decision Trees, maximum depth 12).
- **Target**: `dead_zone_risk`
  - `0`: `NOT_DEAD_ZONE`
  - `1`: `POTENTIAL_DEAD_ZONE`
- **Multi-Feature Ground Truth**:
  A sample is labeled positive if composite degradation occurs:
  $$(\text{RSSI} < -78 \land (\text{Latency} > 110 \lor \text{Loss} > 14\% \lor \text{Throughput} < 6)) \lor (\text{Latency} > 160 \land \text{Loss} > 18\%) \lor (\text{RSSI} < -84)$$
- **Train/Test Split**: 75% training, 25% test, stratified by class ratio.
- **Evaluation**: Genuine computation of Accuracy, Precision, Recall, F1-Score, Confusion Matrix, and Gini Feature Importance.

---

## 4. Grid Prediction Map

1. A uniform spatial lattice of $2.0\text{m} \times 2.0\text{m}$ resolution is established across the building floorplan ($80\text{m} \times 50\text{m}$).
2. For each unmeasured grid coordinate:
   - RF propagation ray-tracing computes estimated RSSI, wall penetration attenuation, and distance.
   - Spatial query computes local AP density.
   - Vector is passed to `model.predict_proba()`.
3. Output produces `dead_zone_probability` $P \in [0.0, 1.0]$ and classification `POTENTIAL_DEAD_ZONE` if $P \ge 0.50$.
