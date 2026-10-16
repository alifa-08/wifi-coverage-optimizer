from typing import List, Tuple, Dict, Any

def evaluate_dead_zone_severity(
    avg_rssi: float,
    avg_latency: float,
    avg_packet_loss: float,
    avg_throughput: float
) -> str:
    """
    Calculate dead-zone severity (LOW, MEDIUM, HIGH, CRITICAL) based on
    a multi-metric composite penalty score.
    """
    penalty = 0.0

    # RSSI Penalty (0 to 35 points)
    if avg_rssi < -88.0:
        penalty += 35.0
    elif avg_rssi < -83.0:
        penalty += 25.0
    elif avg_rssi < -78.0:
        penalty += 15.0
    else:
        penalty += 5.0

    # Latency Penalty (0 to 25 points)
    if avg_latency > 250.0:
        penalty += 25.0
    elif avg_latency > 180.0:
        penalty += 18.0
    elif avg_latency > 120.0:
        penalty += 10.0
    else:
        penalty += 3.0

    # Packet Loss Penalty (0 to 25 points)
    if avg_packet_loss > 30.0:
        penalty += 25.0
    elif avg_packet_loss > 20.0:
        penalty += 18.0
    elif avg_packet_loss > 12.0:
        penalty += 10.0
    else:
        penalty += 3.0

    # Throughput Penalty (0 to 15 points)
    if avg_throughput < 1.0:
        penalty += 15.0
    elif avg_throughput < 3.0:
        penalty += 10.0
    elif avg_throughput < 6.0:
        penalty += 5.0

    if penalty >= 75.0:
        return "CRITICAL"
    elif penalty >= 52.0:
        return "HIGH"
    elif penalty >= 32.0:
        return "MEDIUM"
    else:
        return "LOW"

def diagnose_contributing_factors(
    avg_rssi: float,
    avg_latency: float,
    avg_packet_loss: float,
    avg_throughput: float,
    avg_distance: float,
    avg_wall_factor: float
) -> List[str]:
    """Diagnose the architectural and physical causes of poor connectivity."""
    factors = []

    if avg_wall_factor >= 20.0:
        factors.append(f"Severe wall attenuation ({avg_wall_factor:.1f} dB loss through multiple concrete/brick partitions)")
    elif avg_wall_factor >= 10.0:
        factors.append(f"Moderate wall penetration loss ({avg_wall_factor:.1f} dB structural obstruction)")

    if avg_distance >= 25.0:
        factors.append(f"Excessive physical distance from nearest AP ({avg_distance:.1f} meters propagation span)")
    elif avg_distance >= 18.0:
        factors.append(f"Borderline AP coverage distance ({avg_distance:.1f} meters)")

    if avg_packet_loss >= 20.0:
        factors.append(f"Severe packet drop rate ({avg_packet_loss:.1f}%) triggering connection drops")

    if avg_latency >= 180.0:
        factors.append(f"High transport latency ({avg_latency:.1f} ms) causing buffer stalls and jitter")

    if avg_throughput < 2.0:
        factors.append(f"Constrained data rate throughput ({avg_throughput:.2f} Mbps) insufficient for modern applications")

    if not factors:
        factors.append("Composite RF path loss attenuation at edge of transmission range")

    return factors
