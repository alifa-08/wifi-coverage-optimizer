"""
Mathematical calculation utilities for Wi-Fi coverage optimization,
Before vs After comparative analysis, and room-level RF telemetry analytics.

Mathematical Conventions:
- Area Reduction: Before - After (positive = improvement, negative = worsening).
- Area Reduction Percentage: ((Before - After) / Before) * 100 (safe 0.0% when Before <= 0).
- Count Reduction: Before - After (positive = eliminated dead zones, negative = increased dead zones).
- RSSI Improvement: After - Before in dB (positive = stronger signal).
- Latency Reduction: Before - After in ms (positive = reduced latency / better performance).
- Packet Loss Reduction: Before - After in % (positive = lower loss / better performance).
- Throughput Improvement: After - Before in Mbps (positive = higher throughput / better performance).
"""

from typing import Dict, Any, List, Optional, Tuple
import math

def calculate_before_after_metrics(
    before_count: int,
    after_count: int,
    before_area: float,
    after_area: float,
    before_good_pct: float,
    after_good_pct: float,
    before_poor_pct: float,
    after_poor_pct: float,
    before_avg_rssi: float,
    after_avg_rssi: float,
    before_avg_latency: float,
    after_avg_latency: float,
    before_avg_loss: float,
    after_avg_loss: float,
    before_avg_throughput: float,
    after_avg_throughput: float
) -> Dict[str, Any]:
    """
    Compute mathematically verified delta metrics between baseline (BEFORE)
    and remediated (AFTER) simulation states.

    NEVER clamps negative values to zero; honors genuine signed deltas.
    Safely handles zero baselines without division-by-zero exceptions.
    """
    # 1. Dead Zone Count Reductions
    count_reduction = int(before_count - after_count)
    if before_count > 0:
        count_red_pct = round(((before_count - after_count) / float(before_count)) * 100.0, 1)
        is_count_pct_undefined = False
    else:
        count_red_pct = 0.0
        is_count_pct_undefined = True

    # 2. Dead Zone Area Reductions
    area_reduction = round(float(before_area - after_area), 1)
    if before_area > 0.0:
        area_red_pct = round(((before_area - after_area) / float(before_area)) * 100.0, 1)
        is_area_pct_undefined = False
    else:
        area_red_pct = 0.0
        is_area_pct_undefined = True

    # 3. RF Signal Quality & Network Performance Deltas
    # Positive delta = Improvement
    rssi_improvement = round(float(after_avg_rssi - before_avg_rssi), 2)
    latency_reduction = round(float(before_avg_latency - after_avg_latency), 2)
    packet_loss_reduction = round(float(before_avg_loss - after_avg_loss), 2)
    throughput_improvement = round(float(after_avg_throughput - before_avg_throughput), 2)

    # 4. Status Determination: Distinguishes undefined zero-baseline from genuine zero-delta improvement
    if before_area <= 0.0:
        if after_area <= 0.0:
            area_reduction_status = "ZERO_BASELINE_CLEAN"
        else:
            area_reduction_status = "ZERO_BASELINE_WORSENED"
    elif area_reduction > 0.0:
        area_reduction_status = "IMPROVED"
    elif area_reduction < 0.0:
        area_reduction_status = "WORSENED"
    else:
        area_reduction_status = "UNCHANGED"

    # Overall Status: Weighted composite evaluation
    if area_reduction > 0.0 or (before_area <= 0.0 and rssi_improvement > 0.5):
        overall_status = "IMPROVED"
    elif area_reduction < 0.0 or rssi_improvement < -3.0 or area_reduction_status == "ZERO_BASELINE_WORSENED":
        overall_status = "WORSENED"
    elif (area_reduction == 0.0 or area_reduction_status == "ZERO_BASELINE_CLEAN") and abs(rssi_improvement) <= 0.5:
        overall_status = "UNCHANGED"
    else:
        overall_status = "INCONCLUSIVE"

    return {
        "before_dead_zone_count": before_count,
        "after_dead_zone_count": after_count,
        "dead_zone_count_reduction": count_reduction,
        "dead_zone_count_reduction_pct": count_red_pct,
        "is_count_pct_undefined": is_count_pct_undefined,
        "before_dead_zone_area": round(float(before_area), 1),
        "after_dead_zone_area": round(float(after_area), 1),
        "dead_zone_area_reduction": area_reduction,
        "dead_zone_area_reduction_pct": area_red_pct,
        "is_area_pct_undefined": is_area_pct_undefined,
        "before_coverage_good_pct": round(float(before_good_pct), 1),
        "after_coverage_good_pct": round(float(after_good_pct), 1),
        "before_coverage_poor_pct": round(float(before_poor_pct), 1),
        "after_coverage_poor_pct": round(float(after_poor_pct), 1),
        "before_avg_rssi": round(float(before_avg_rssi), 2),
        "after_avg_rssi": round(float(after_avg_rssi), 2),
        "rssi_improvement": rssi_improvement,
        "before_avg_latency": round(float(before_avg_latency), 2),
        "after_avg_latency": round(float(after_avg_latency), 2),
        "latency_reduction": latency_reduction,
        "before_avg_packet_loss": round(float(before_avg_loss), 2),
        "after_avg_packet_loss": round(float(after_avg_loss), 2),
        "packet_loss_reduction": packet_loss_reduction,
        "before_avg_throughput": round(float(before_avg_throughput), 2),
        "after_avg_throughput": round(float(after_avg_throughput), 2),
        "throughput_improvement": throughput_improvement,
        "status": overall_status,
        "area_reduction_status": area_reduction_status,
    }


def classify_room_health(
    avg_rssi: Optional[float],
    avg_latency: Optional[float],
    avg_packet_loss: Optional[float],
    poor_ratio: Optional[float],
    points_count: int
) -> str:
    """
    Classify the health status of a room based on multi-parameter RF telemetry.

    Health Categories:
    - NO_DATA: Zero sample points inside the room or missing RSSI.
    - INCOMPLETE_DATA: Points exist, but essential latency or loss telemetry is missing (never evaluated as OPTIMAL).
    - CRITICAL: Severe dead-zone coverage (RSSI < -82 dBm or poor_ratio > 35%).
    - DEGRADED: Noticeable signal degradation (RSSI < -75 dBm, poor_ratio > 15%, loss > 10%, latency > 120ms).
    - MODERATE: Acceptable but sub-optimal (RSSI < -70 dBm, poor_ratio > 5%, loss > 5%, latency > 80ms).
    - OPTIMAL: Pristine signal (RSSI >= -70 dBm, loss <= 5%, latency <= 80ms, poor_ratio <= 5%).

    Boundary Guarantees:
    - Zero measurements ALWAYS returns 'NO_DATA'.
    - Missing metrics NEVER silently default to zero.
    - Incomplete telemetry NEVER produces 'OPTIMAL'.
    - Weak RSSI (< -75 dBm) NEVER produces 'OPTIMAL'.
    - High packet loss (> 5%) or latency (> 100ms) NEVER produces 'OPTIMAL'.
    """
    if points_count <= 0 or avg_rssi is None:
        return "NO_DATA"

    poor = poor_ratio if poor_ratio is not None else 0.0

    # 1. Critical Dead Zone Threshold (evaluated on available telemetry)
    if avg_rssi < -82.0 or poor > 35.0:
        return "CRITICAL"

    # 2. Degraded Connectivity Threshold
    if (
        avg_rssi < -75.0 or
        poor > 15.0 or
        (avg_packet_loss is not None and avg_packet_loss > 10.0) or
        (avg_latency is not None and avg_latency > 120.0)
    ):
        return "DEGRADED"

    # 3. Moderate Threshold
    if (
        avg_rssi < -70.0 or
        poor > 5.0 or
        (avg_packet_loss is not None and avg_packet_loss > 5.0) or
        (avg_latency is not None and avg_latency > 80.0)
    ):
        return "MODERATE"

    # 4. Incomplete Telemetry Guard:
    # If latency or packet loss is missing, we CANNOT certify OPTIMAL health.
    # Missing values must never silently become zero or result in OPTIMAL classification.
    if avg_latency is None or avg_packet_loss is None:
        return "INCOMPLETE_DATA"

    # 5. Optimal Threshold (strictly enforced across ALL verified parameters)
    return "OPTIMAL"
