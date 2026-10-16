# Access Point Optimization & Verification

## 1. AP Recommendation Objective

The AP recommendation module is strictly designed around **dead-zone relief**. Rather than distributing routers uniformly, it targets candidate AP placements to eliminate high-severity dead-zone cores and under-served room centroids.

---

## 2. Candidate Generation

1. **Dead-Zone Centroids**: Evaluates coordinates at the center of mass $(\bar{x}, \bar{y})$ of each detected dead-zone polygon.
2. **Room Centroids**: Evaluates geometric centers of enclosed rooms exhibiting degraded reception.
3. **Spatial Separation Filter**: Enforces a minimum distance of $18.0\text{ meters}$ between recommended APs and existing active APs to prevent co-channel interference and hardware redundancy.

---

## 3. Placement Simulation & Ranking

For each candidate position $(x_c, y_c)$:
1. A candidate AP is temporarily injected into the simulation pool with $P_{tx} = 20\text{ dBm}$.
2. RF propagation is re-simulated across degraded measurement samples.
3. Re-calculated quality metrics determine:
   - Recovered measurement points.
   - Relieved ratio: $\frac{\text{Poor Points Recovered}}{\text{Baseline Poor Points}}$.
   - Expected Dead-Zone Area Reduction ($m^2$): $\text{Relieved Ratio} \times \text{Baseline Dead Zone Area}$.
   - Expected Dead-Zone Count Reduction.
4. Candidates are sorted descending by recovered area. Top candidates receive Priority 1 and Priority 2 ratings with descriptive rationale text.

---

## 4. Before vs After Verification

The comparative verification step runs a dual-simulation benchmark:
1. **BEFORE**: Evaluates baseline dead-zone count, total dead-zone area ($m^2$), good coverage ratio (%), average RSSI, latency, packet loss, and throughput.
2. **AFTER**: Automatically applies top recommended APs, simulates physical RF reception, and runs dead-zone clustering on the optimized network.
3. **Impact Verification**:
   - $\Delta \text{Dead-Zone Area} = \text{Area}_{\text{before}} - \text{Area}_{\text{after}}$
   - $\%\text{ Area Reduction} = \frac{\Delta \text{Area}}{\text{Area}_{\text{before}}} \times 100\%$
   - $\Delta \text{Dead-Zone Count} = \text{Count}_{\text{before}} - \text{Count}_{\text{after}}$
   - RSSI Gain, Latency Reduction, and Packet Loss Drop.
