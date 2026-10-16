# Dead-Zone Detection & Diagnostics Methodology

## 1. What Defines a Dead Zone?

A single isolated poor measurement does **not** constitute a Wi-Fi dead zone. Temporary interference, channel collisions, or transient client shielding may cause momentary packet drops.

In this system, a **Dead Zone** represents a **continuous spatial region with consistently degraded wireless connectivity**, characterized by:
1. Spatial aggregation of multiple adjacent degraded measurement points.
2. Deficient multi-parameter network quality:
   - $\text{RSSI} < -78\text{ dBm}$ (borderline reception)
   - Round-trip latency $> 120\text{ ms}$
   - Packet loss $> 15\%$
   - Throughput $< 5\text{ Mbps}$

---

## 2. Spatial Clustering Algorithm (DBSCAN)

Degraded sample coordinates are clustered using **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)**:
- Metric: Euclidean 2D distance.
- Epsilon Neighborhood ($\epsilon$): $6.0\text{ meters}$.
- Min Samples: 3 sample points.

Points identified as noise (label $-1$) are discarded, guaranteeing that solitary anomalies are excluded from dead-zone declarations.

---

## 3. Boundary Polygon & Area Computation

For each cluster $C$:
1. **Convex Hull**: Monotone Chain algorithm generates the minimal enclosing convex polygon $H(C)$.
2. **Affected Floor Area**:
   $$\text{Area} = \max\left(\text{ShoelaceArea}(H(C)), |C| \times d_{\text{cell}}^2\right)$$
   Where each grid measurement represents $4.0\text{ m}^2$ ($2.0\text{m} \times 2.0\text{m}$) of physical floor surface area.
3. **Center of Mass**: Arithmetic mean $(\bar{x}, \bar{y})$ of clustered coordinates.

---

## 4. Multi-Metric Severity Scoring

Dead-zone severity is categorized into four tiers based on a composite multi-parameter penalty $S_{\text{penalty}} \in [0, 100]$:

| Metric | Range for Penalty | Max Penalty Contribution |
|---|---|---|
| **RSSI** | $-78\text{ dBm}$ down to $<-88\text{ dBm}$ | $35\text{ points}$ |
| **Latency** | $120\text{ ms}$ up to $>250\text{ ms}$ | $25\text{ points}$ |
| **Packet Loss** | $12\%$ up to $>30\%$ | $25\text{ points}$ |
| **Throughput** | $6\text{ Mbps}$ down to $<1\text{ Mbps}$ | $15\text{ points}$ |

### Severity Thresholds:
- **CRITICAL** ($S \ge 75$): Complete disconnection or severe packet stalls. Requires immediate AP remediation.
- **HIGH** ($52 \le S < 75$): Frequent connection drops and unworkable latency.
- **MEDIUM** ($32 \le S < 52$): Sluggish response, streaming buffering, video conferencing degradation.
- **LOW** ($S < 32$): Edge reception degradation with functional baseline connectivity.

---

## 5. Root-Cause Diagnosis

The diagnostic engine inspects structural geometry and RF path factors to explain *why* the dead zone formed:
- **Severe Wall Attenuation**: $\sum L_w \ge 20\text{ dB}$ through multiple dense concrete or brick partitions.
- **Excessive Physical Distance**: Propagation span $\ge 25\text{ meters}$ beyond AP transmission range.
- **Severe Packet Loss Spikes**: Drop rates $> 20\%$ causing TCP retransmissions.
- **High Transport Latency**: RTT $> 180\text{ ms}$ causing jitter and buffer stalls.

---

## 6. Persistence Tracking

When multiple simulation runs occur over the same building floor:
$$\text{Persistence Score} = \frac{\text{Historical Matching Runs} + 1}{\text{Total Prior Runs} + 1}$$
Dead zones exhibiting $\ge 2$ historical recurrences or persistence scores $\ge 40\%$ are flagged as **Persistent Dead Zones**, triggering automated administrative warnings in the Alert Center.
