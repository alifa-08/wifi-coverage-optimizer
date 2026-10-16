import re
import subprocess
import platform
from typing import Dict, Any, Optional, Tuple

def parse_netsh_output(output: str) -> Dict[str, Any]:
    """
    Parse raw output from `netsh wlan show interfaces` and extract Wi-Fi adapter fields.
    """
    if not output or "State" not in output:
        return {
            "connected": False,
            "error": "No Wi-Fi interface detected or adapter disabled.",
            "ssid": None,
            "bssid": None,
            "signal_percent": None,
            "rssi_dbm": None,
            "is_rssi_estimated": True,
            "channel": None,
            "band": None,
            "radio_type": None,
            "link_speed_mbps": None,
        }

    def extract_field(pattern: str) -> Optional[str]:
        m = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else None

    state = extract_field(r"State\s*:\s*(.+)")
    is_connected = bool(state and "connected" in state.lower() and "disconnected" not in state.lower())

    if not is_connected:
        return {
            "connected": False,
            "state": state or "disconnected",
            "error": "Wi-Fi adapter is not connected to any network.",
            "ssid": None,
            "bssid": None,
            "signal_percent": None,
            "rssi_dbm": None,
            "is_rssi_estimated": True,
            "channel": None,
            "band": None,
            "radio_type": None,
            "link_speed_mbps": None,
        }

    ssid = extract_field(r"SSID\s*:\s*([^\r\n]+)")
    bssid = extract_field(r"(?:AP BSSID|BSSID)\s*:\s*([^\r\n]+)")
    radio_type = extract_field(r"Radio type\s*:\s*(.+)")
    band = extract_field(r"Band\s*:\s*(.+)")
    channel_str = extract_field(r"Channel\s*:\s*(\d+)")
    signal_str = extract_field(r"Signal\s*:\s*(\d+)%")
    rssi_str = extract_field(r"Rssi\s*:\s*(-?\d+)")
    rx_str = extract_field(r"Receive rate \(Mbps\)\s*:\s*([\d\.]+)")
    tx_str = extract_field(r"Transmit rate \(Mbps\)\s*:\s*([\d\.]+)")

    channel = int(channel_str) if channel_str else None
    signal_pct = float(signal_str) if signal_str else None

    # Determine RSSI: hardware driver reported dBm vs standard approximation
    # Microsoft standard formula: dBm ≈ (signal_pct / 2) - 100
    if rssi_str:
        rssi_dbm = float(rssi_str)
        is_estimated = False
    elif signal_pct is not None:
        rssi_dbm = round((signal_pct / 2.0) - 100.0, 1)
        is_estimated = True
    else:
        rssi_dbm = None
        is_estimated = True

    # Link speed
    rx_rate = float(rx_str) if rx_str else None
    tx_rate = float(tx_str) if tx_str else None
    link_speed = max(filter(None, [rx_rate, tx_rate]), default=None)

    return {
        "connected": True,
        "state": state,
        "ssid": ssid,
        "bssid": bssid,
        "signal_percent": signal_pct,
        "signal_unit": "%",
        "rssi_dbm": rssi_dbm,
        "is_rssi_estimated": is_estimated,
        "channel": channel,
        "band": band or ("5 GHz" if (channel and channel > 14) else "2.4 GHz"),
        "radio_type": radio_type,
        "rx_rate_mbps": rx_rate,
        "tx_rate_mbps": tx_rate,
        "link_speed_mbps": link_speed,
    }

def get_windows_wifi_info() -> Dict[str, Any]:
    """
    Query real Windows Wi-Fi adapter telemetry using native `netsh wlan show interfaces`.
    Extracts connected SSID, BSSID, Radio Type, Band, Channel, Signal percentage,
    hardware RSSI (if driver reports it), and Wi-Fi link speed (Rx/Tx rate).
    """
    if platform.system() != "Windows":
        return {
            "connected": False,
            "error": "Real Wi-Fi survey collection is supported natively on Windows.",
            "ssid": None,
            "bssid": None,
            "signal_percent": None,
            "rssi_dbm": None,
            "is_rssi_estimated": True,
            "channel": None,
            "band": None,
            "radio_type": None,
            "link_speed_mbps": None,
        }

    try:
        proc = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        output = proc.stdout
    except Exception as e:
        return {
            "connected": False,
            "error": f"Failed to execute netsh command: {str(e)}",
            "ssid": None,
            "bssid": None,
            "signal_percent": None,
            "rssi_dbm": None,
            "is_rssi_estimated": True,
            "channel": None,
            "band": None,
            "radio_type": None,
            "link_speed_mbps": None,
        }

    return parse_netsh_output(output)

def get_default_gateway() -> Optional[str]:
    """Retrieve IPv4 default gateway address on Windows."""
    try:
        # Try PowerShell Get-NetRoute
        ps_cmd = "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1 -ExpandProperty NextHop"
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=4,
            check=False
        )
        gw = proc.stdout.strip()
        if gw and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", gw):
            return gw
    except Exception:
        pass

    try:
        # Fallback: parse ipconfig
        proc = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=4, check=False)
        m = re.search(r"Default Gateway[ .]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", proc.stdout)
        if m:
            return m.group(1).strip()
    except Exception:
        pass

    return None

def parse_ping_output(output: str) -> Dict[str, Any]:
    """
    Parse raw output from Windows `ping` command.
    """
    if not output:
        return {
            "success": False,
            "latency_ms": None,
            "packet_loss_percent": 100.0,
        }

    # Parse packet loss
    loss_m = re.search(r"\((\d+)%\s*loss\)", output, re.IGNORECASE)
    if not loss_m:
        loss_m = re.search(r"(\d+)%\s*packet loss", output, re.IGNORECASE)
    packet_loss = float(loss_m.group(1)) if loss_m else (100.0 if "Destination host unreachable" in output else 0.0)

    # Parse average latency
    avg_m = re.search(r"Average\s*=\s*(\d+)\s*ms", output, re.IGNORECASE)
    latency_ms = float(avg_m.group(1)) if avg_m else None

    # If completely lost
    if packet_loss == 100.0:
        latency_ms = None

    return {
        "success": packet_loss < 100.0,
        "latency_ms": latency_ms,
        "packet_loss_percent": packet_loss,
    }

def measure_network_latency(target: Optional[str] = None, count: int = 3) -> Dict[str, Any]:
    """
    Measure local network round-trip ping latency and packet loss.
    Defaults to the local default gateway to isolate wireless link performance from external internet congestion.
    """
    target_type = "custom"
    if not target or target.strip().lower() in ("auto", "gateway", "default"):
        gateway_ip = get_default_gateway()
        if gateway_ip:
            target = gateway_ip
            target_type = "local_gateway"
        else:
            target = "127.0.0.1"
            target_type = "loopback_fallback"
    elif target in ("8.8.8.8", "1.1.1.1"):
        target_type = "internet"

    try:
        proc = subprocess.run(
            ["ping", "-n", str(count), "-w", "1000", target],
            capture_output=True,
            text=True,
            timeout=count * 2 + 2,
            check=False
        )
        out = proc.stdout
    except Exception as e:
        return {
            "success": False,
            "target": target,
            "target_type": target_type,
            "latency_ms": None,
            "packet_loss_percent": 100.0,
            "error": str(e)
        }

    parsed = parse_ping_output(out)
    parsed["target"] = target
    parsed["target_type"] = target_type
    return parsed

def evaluate_real_measurement_quality(
    signal_pct: Optional[float] = None,
    rssi_dbm: Optional[float] = None,
    latency_ms: Optional[float] = None,
    packet_loss_pct: Optional[float] = None,
    signal_percent: Optional[float] = None,
    packet_loss: Optional[float] = None,
) -> Tuple[float, str]:
    """
    Categorize real network quality (GOOD, MODERATE, POOR) based on actual collected measurements.
    """
    if signal_pct is None and signal_percent is not None:
        signal_pct = signal_percent
    if packet_loss_pct is None and packet_loss is not None:
        packet_loss_pct = packet_loss

    if rssi_dbm is None and signal_pct is not None:
        rssi_dbm = (signal_pct / 2.0) - 100.0

    eff_rssi = rssi_dbm if rssi_dbm is not None else -95.0
    eff_lat = latency_ms if latency_ms is not None else 300.0
    eff_loss = packet_loss_pct if packet_loss_pct is not None else 50.0

    if eff_rssi >= -65.0 and eff_lat <= 50.0 and eff_loss <= 2.0:
        score = 85.0 + max(0.0, min(15.0, (eff_rssi + 65.0) * 0.5))
        return round(score, 1), "GOOD"
    elif eff_rssi >= -78.0 and eff_lat <= 120.0 and eff_loss <= 10.0:
        score = 55.0 + ((eff_rssi + 78.0) / 13.0) * 25.0
        return round(max(50.0, min(84.0, score)), 1), "MODERATE"
    else:
        score = max(5.0, 45.0 - (max(0.0, -78.0 - eff_rssi) * 2.0) - (eff_loss * 0.5))
        return round(score, 1), "POOR"
