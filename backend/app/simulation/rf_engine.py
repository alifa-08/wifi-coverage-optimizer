import math
import random
from typing import List, Dict, Any, Tuple, Optional
from app.utils.geometry import segments_intersect, point_distance

class RFEngine:
    """
    Physics-informed RF propagation simulation engine using the Multi-Wall
    Cost-231 / ITU-R Indoor Path Loss Model with correlated network metrics.
    """
    def __init__(
        self,
        reference_loss_1m: float = 40.0, # dB loss at 1 meter for 2.4 GHz
        path_loss_exponent: float = 3.0, # Indoor multi-partition path loss exponent
        noise_std_dev: float = 1.8       # Shadowing standard deviation (dB)
    ):
        self.reference_loss_1m = reference_loss_1m
        self.path_loss_exponent = path_loss_exponent
        self.noise_std_dev = noise_std_dev

    def calculate_wall_attenuation(
        self,
        ap_pos: Tuple[float, float],
        point_pos: Tuple[float, float],
        walls: List[Dict[str, Any]]
    ) -> float:
        """Calculate cumulative wall attenuation between AP and point by ray-tracing."""
        total_attenuation = 0.0
        for wall in walls:
            w_p1 = (wall["x1"], wall["y1"])
            w_p2 = (wall["x2"], wall["y2"])
            if segments_intersect(ap_pos, point_pos, w_p1, w_p2):
                total_attenuation += wall.get("attenuation_db", 10.0)
        return total_attenuation

    def compute_received_power(
        self,
        ap: Dict[str, Any],
        point: Tuple[float, float],
        walls: List[Dict[str, Any]],
        add_noise: bool = True
    ) -> Tuple[float, float, float]:
        """
        Compute RSSI from a specific AP to a receiver coordinate.
        Returns (rssi, distance, wall_attenuation).
        """
        ap_pos = (ap["x"], ap["y"])
        dist = max(point_distance(ap_pos, point), 0.5) # Minimum distance clamp 0.5m
        tx_power = ap.get("tx_power_dbm", 20.0)

        # Distance path loss: PL(d) = PL(1m) + 10 * n * log10(d)
        dist_loss = self.reference_loss_1m + 10.0 * self.path_loss_exponent * math.log10(dist)

        # Obstacle attenuation
        wall_atten = self.calculate_wall_attenuation(ap_pos, point, walls)

        # Log-normal shadowing noise
        noise = random.gauss(0, self.noise_std_dev) if add_noise else 0.0

        total_loss = dist_loss + wall_atten - noise
        rssi = tx_power - total_loss

        # Clamp RSSI to physical reality (-100 dBm noise floor to -15 dBm very close)
        rssi = max(-98.0, min(-20.0, rssi))
        return round(rssi, 2), round(dist, 2), round(wall_atten, 2)

    def calculate_network_metrics(
        self,
        rssi: float,
        add_noise: bool = True
    ) -> Tuple[float, float, float, float, str]:
        """
        Derive logically correlated Wi-Fi performance metrics based on RSSI:
        Returns (latency_ms, packet_loss_pct, throughput_mbps, quality_score, quality_category).
        """
        # RSSI ranges:
        # Excellent: > -60 dBm
        # Good: -60 to -70 dBm
        # Moderate: -70 to -78 dBm
        # Poor / Dead Zone: < -78 dBm

        if rssi >= -65.0:
            # Good signal conditions
            base_latency = 12.0 + ((-65.0 - rssi) * 0.4)
            base_packet_loss = 0.2 + ((-65.0 - rssi) * 0.08)
            base_throughput = 220.0 - ((-65.0 - rssi) * 3.5)
            quality_score = 80.0 + ((rssi + 65.0) / 45.0) * 20.0
            category = "GOOD"
        elif rssi >= -78.0:
            # Moderate signal conditions
            norm = (rssi - (-78.0)) / 13.0 # 0 to 1
            base_latency = 75.0 - (norm * 45.0)
            base_packet_loss = 7.0 - (norm * 5.5)
            base_throughput = 30.0 + (norm * 80.0)
            quality_score = 50.0 + (norm * 29.0)
            category = "MODERATE"
        else:
            # Poor / Dead Zone conditions
            deficit = -78.0 - rssi # e.g. 0 to 20 dBm deficit
            base_latency = 130.0 + (deficit * 14.0)
            base_packet_loss = 16.0 + (deficit * 2.8)
            base_throughput = max(0.2, 12.0 - (deficit * 0.8))
            quality_score = max(5.0, 48.0 - (deficit * 2.5))
            category = "POOR"

        if add_noise:
            latency = max(8.0, base_latency + random.gauss(0, 3.5))
            packet_loss = max(0.0, min(100.0, base_packet_loss + random.gauss(0, 0.8)))
            throughput = max(0.1, base_throughput + random.gauss(0, 4.0))
        else:
            latency = base_latency
            packet_loss = max(0.0, min(100.0, base_packet_loss))
            throughput = max(0.1, base_throughput)

        quality_score = max(0.0, min(100.0, quality_score))

        return (
            round(latency, 2),
            round(packet_loss, 2),
            round(throughput, 2),
            round(quality_score, 1),
            category
        )

    def simulate_point(
        self,
        point: Tuple[float, float],
        active_aps: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        add_noise: bool = True
    ) -> Dict[str, Any]:
        """
        Simulate Wi-Fi reception at a specific coordinate against all active APs.
        The client connects to the AP providing the highest received signal power (best RSSI).
        """
        if not active_aps:
            return {
                "x": point[0],
                "y": point[1],
                "ap_id": None,
                "rssi": -98.0,
                "latency": 500.0,
                "packet_loss": 99.0,
                "throughput": 0.0,
                "distance_to_ap": 99.0,
                "wall_factor": 50.0,
                "quality_score": 0.0,
                "quality_category": "POOR"
            }

        best_rssi = -999.0
        best_ap_id = None
        best_dist = 999.0
        best_wall_factor = 0.0

        for ap in active_aps:
            rssi, dist, wall_atten = self.compute_received_power(ap, point, walls, add_noise=add_noise)
            if rssi > best_rssi:
                best_rssi = rssi
                best_ap_id = ap["id"]
                best_dist = dist
                best_wall_factor = wall_atten

        latency, p_loss, tput, q_score, category = self.calculate_network_metrics(
            best_rssi, add_noise=add_noise
        )

        return {
            "x": point[0],
            "y": point[1],
            "ap_id": best_ap_id,
            "rssi": best_rssi,
            "latency": latency,
            "packet_loss": p_loss,
            "throughput": tput,
            "distance_to_ap": best_dist,
            "wall_factor": best_wall_factor,
            "quality_score": q_score,
            "quality_category": category
        }
