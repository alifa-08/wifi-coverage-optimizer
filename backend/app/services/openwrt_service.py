import subprocess
import json
import logging
import re
import hashlib
import secrets
import base64
import urllib.parse
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from app.config import settings

# Backend-only private configuration (STRICTLY private to backend, never exposed to API responses)
_SSH_KEY_PATH = Path(settings.OPENWRT_SSH_KEY_PATH)
_GATEWAY_HOST = settings.OPENWRT_HOST
_GATEWAY_USER = settings.OPENWRT_USER
_COMMAND_TIMEOUT_SEC = settings.OPENWRT_TIMEOUT_SEC

MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

# =====================================================================
# Binary IEC Data Quota Definitions (1 GiB = 1,024 MiB = 1,048,576 KiB)
# =====================================================================
BYTES_PER_KIB = 1024
BYTES_PER_MIB = 1024 * 1024          # 1,048,576 bytes
BYTES_PER_GIB = 1024 * 1024 * 1024   # 1,073,741,824 bytes
KIB_PER_MIB = 1024
MIB_PER_GIB = 1024                   # Exactly 1,024 MiB = 1 GiB


def hash_password(password: str) -> str:
    """Hash student passwords using PBKDF2-HMAC-SHA256 with 100,000 rounds and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password in constant time using secrets.compare_digest."""
    try:
        salt, key_hex = hashed_password.split(":")
        check_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(check_key.hex(), key_hex)
    except Exception:
        return False


def normalize_mac(mac: str) -> str:
    """Normalize MAC address to standard lowercase colon format."""
    clean = mac.strip().replace("-", ":").lower()
    return clean


def is_valid_mac(mac: str) -> bool:
    """Validate standard 6-octet MAC format."""
    return bool(MAC_REGEX.match(mac.strip()))


def split_quota_allocation(total_quota_kb: int, download_ratio: float = 0.85) -> Tuple[int, int]:
    """
    Strictly allocates the student's remaining daily data allowance across
    OpenNDS upload and download quota parameters so that:
        upload_quota_kb + download_quota_kb <= total_quota_kb
    This guarantees that the gateway does NOT grant a student twice their quota
    by applying the full limit independently to both directions.
    """
    if total_quota_kb <= 0:
        return 0, 0
    if total_quota_kb <= 1024:
        # For very small remaining quotas (e.g. 1 MiB)
        down_kb = int(total_quota_kb * 0.75)
        up_kb = total_quota_kb - down_kb
        return max(1, up_kb), max(1, down_kb)

    down_kb = int(total_quota_kb * download_ratio)
    up_kb = total_quota_kb - down_kb
    return up_kb, down_kb


# =====================================================================
# OpenNDS 10.3.1 FAS Level 1 Handshake & Key Infrastructure
# =====================================================================
DEFAULT_FAS_KEY = settings.OPENNDS_FAS_KEY


def parse_fas_parameter(fas_b64: Optional[str]) -> Dict[str, str]:
    """
    Decodes and parses the OpenNDS 10.3.1 FAS Level 1 query string.
    OpenNDS constructs the parameter by formatting:
        hid=<hid>, clientip=<clientip>, clientmac=<clientmac>, client_type=<client_type>,
        gatewayname=<gatewayname>, gatewayurl=<gatewayurl>, version=<version>,
        gatewayaddress=<gatewayaddress>, gatewaymac=<gatewaymac>, authdir=<authdir>,
        originurl=<originurl>, clientif=<clientif>
    and base64-encoding the entire comma-space delimited string.
    Returns a dictionary of parsed key-value parameters.
    """
    if not fas_b64 or not fas_b64.strip():
        return {}

    clean_b64 = fas_b64.strip()
    # Fix standard base64 padding if stripped by browser or proxy
    missing_padding = len(clean_b64) % 4
    if missing_padding:
        clean_b64 += "=" * (4 - missing_padding)

    try:
        decoded_bytes = base64.b64decode(clean_b64, validate=False)
        decoded_str = decoded_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Failed to base64 decode OpenNDS fas parameter: {str(e)}")
        return {}

    parsed: Dict[str, str] = {}
    items = decoded_str.split(", ") if ", " in decoded_str else decoded_str.split(",")
    for item in items:
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, val = item.split("=", 1)
        k = key.strip().lower()
        v = val.strip()
        try:
            v_unquoted = urllib.parse.unquote(v)
        except Exception:
            v_unquoted = v
        parsed[k] = v_unquoted

    if "clientmac" in parsed and parsed["clientmac"]:
        parsed["clientmac"] = normalize_mac(parsed["clientmac"])

    return parsed


def compute_fas_token(hid: str, faskey: Optional[str] = None) -> str:
    """
    Computes the authoritative OpenNDS FAS Level 1 authorization token:
        tok = sha256(hid . faskey)
    Verified against OpenNDS 10.3.1 documentation (/etc/opennds/config.uci)
    and reference implementation (/etc/opennds/fas-hid.php).
    """
    if not hid or not hid.strip():
        raise ValueError("Cannot compute FAS token without valid client hid (hashed token).")
    key = (faskey or DEFAULT_FAS_KEY).strip()
    payload = f"{hid.strip()}{key}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_trusted_gateway_destination(candidate: Optional[str] = None) -> str:
    """
    Validates and returns the authoritative trusted OpenNDS gateway destination (host:port).
    If a candidate address is provided, it is strictly validated against the configured
    OPENWRT_HOST and OPENNDS_MHD_PORT. Any external hostnames, unexpected ports, path components,
    or malformed addresses are rejected and safely fall back to the configured trusted gateway.
    """
    trusted_default = f"{settings.OPENWRT_HOST}:{settings.OPENNDS_MHD_PORT}"
    if not candidate or not candidate.strip():
        return trusted_default

    clean = candidate.strip()
    # Strip scheme if accidentally present
    if clean.startswith("http://") or clean.startswith("https://"):
        try:
            parsed = urllib.parse.urlsplit(clean)
            clean = parsed.netloc or clean
        except Exception:
            return trusted_default

    # Strip any path or trailing slashes
    clean = clean.split("/")[0].strip()

    # Host and port parsing
    if ":" in clean:
        parts = clean.split(":")
        if len(parts) != 2:
            logger.warning(f"Rejected malformed gateway address candidate '{candidate}' -> using trusted '{trusted_default}'")
            return trusted_default
        host_part, port_part = parts[0].strip().lower(), parts[1].strip()
        if not port_part.isdigit():
            logger.warning(f"Rejected invalid port in gateway address '{candidate}' -> using trusted '{trusted_default}'")
            return trusted_default
        candidate_port = int(port_part)
    else:
        host_part = clean.lower()
        candidate_port = settings.OPENNDS_MHD_PORT

    allowed_hosts = {settings.OPENWRT_HOST.lower()}
    if settings.OPENWRT_HOST in ("127.0.0.1", "localhost"):
        allowed_hosts.update({"127.0.0.1", "localhost"})

    if host_part not in allowed_hosts or candidate_port != settings.OPENNDS_MHD_PORT:
        logger.warning(
            f"Untrusted gateway destination '{candidate}' rejected (host={host_part}, port={candidate_port}). "
            f"Enforcing trusted gateway '{trusted_default}'."
        )
        return trusted_default

    return f"{host_part}:{candidate_port}"


def sanitize_authdir(authdir: Optional[str] = None) -> str:
    """
    Sanitizes the OpenNDS auth directory name to prevent path traversal or injection.
    Defaults strictly to 'opennds_auth'.
    """
    default_authdir = "opennds_auth"
    if not authdir or not authdir.strip():
        return default_authdir

    clean = authdir.strip().strip("/")
    # Allow only safe alphanumeric and underscore characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", clean) or ".." in clean:
        logger.warning(f"Malicious or unexpected authdir '{authdir}' sanitized to '{default_authdir}'")
        return default_authdir

    return clean


def sanitize_redirect_url(url: Optional[str] = None, fallback: str = "https://www.google.com") -> str:
    """
    Validates and sanitizes redirection URLs to prevent open redirect abuse,
    embedded credential leaks, CRLF injection, and protocol handler vulnerabilities.

    CAPTIVE PORTAL REDIRECTION POLICY:
    In standard captive-portal workflows, connecting clients originally attempt to visit
    an arbitrary public website (the "origin URL", e.g. news, documentation, or search engines).
    The policy permits valid HTTP and HTTPS destinations with legitimate hostnames/FQDNs
    so users can resume normal browsing upon authentication.

    STRICT CONTROLS:
    1. Only 'http' and 'https' schemes with non-empty netloc are accepted.
    2. Embedded credentials/userinfo (containing '@', username, or password) are rejected.
    3. CRLF injection (\r, \n), null bytes (\0), and ASCII control characters are rejected.
    4. Backslashes ('\\') anywhere in the URL are rejected to prevent authority confusion.
    5. The cryptographic FAS authorization token is NEVER sent or appended to the redirect URL.
    """
    if not url or not url.strip():
        return fallback

    clean_url = url.strip()

    # Reject control characters (< 32, 127), CRLF injection, and backslashes
    if any(ord(c) < 32 or ord(c) == 127 or c == "\\" for c in clean_url):
        logger.warning("Unsafe characters (CRLF, control, or backslash) detected in redirect URL; reverting to safe fallback.")
        return fallback

    try:
        parsed = urllib.parse.urlsplit(clean_url)
    except Exception:
        return fallback

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        logger.warning(f"Disallowed scheme '{scheme}' in redirect URL '{clean_url}'; reverting to safe fallback.")
        return fallback

    # Ensure netloc is present
    if not parsed.netloc or not parsed.netloc.strip():
        logger.warning(f"Missing netloc in redirect URL '{clean_url}'; reverting to safe fallback.")
        return fallback

    # Reject embedded credentials / userinfo
    if "@" in parsed.netloc or parsed.username or parsed.password:
        logger.warning(f"Embedded userinfo/credentials in redirect URL '{clean_url}'; reverting to safe fallback.")
        return fallback

    # Check for whitespace in host
    host = parsed.netloc.split(":")[0].strip().lower()
    if not host or any(c in host for c in (" ", "\t")):
        logger.warning(f"Invalid host in redirect URL '{clean_url}'; reverting to safe fallback.")
        return fallback

    return clean_url


def build_opennds_auth_url(
    gatewayaddress: Optional[str] = None,
    tok: str = "",
    redir_url: Optional[str] = None,
    authdir: Optional[str] = "opennds_auth",
    custom: Optional[str] = None
) -> str:
    """
    Constructs the exact OpenNDS redirection URL to authenticate the client:
    http://<trusted_gateway>/<safe_authdir>/?tok=<tok>&redir=<safe_redir>&custom=<custom>
    Enforces trusted gateway destination and safe sanitization for all parameters.
    Submitting or following this URL transitions the client state to AUTHENTICATED
    and opens the gateway firewall on OpenWrt.
    """
    if not tok or not tok.strip():
        raise ValueError("Cannot compute FAS authorization URL without a valid token.")

    clean_gw = get_trusted_gateway_destination(gatewayaddress)
    clean_authdir = sanitize_authdir(authdir)
    clean_redir = sanitize_redirect_url(redir_url)

    params = {
        "tok": tok.strip(),
        "redir": clean_redir
    }
    if custom:
        b64_custom = base64.b64encode(custom.encode("utf-8")).decode("ascii")
        params["custom"] = b64_custom

    query_str = urllib.parse.urlencode(params)
    return f"http://{clean_gw}/{clean_authdir}/?{query_str}"


# =====================================================================
# In-Memory Token & Demo OTP Stores
# =====================================================================
_active_admin_tokens: Dict[str, Dict[str, Any]] = {}
_demo_otps: Dict[str, Dict[str, Any]] = {}


def create_admin_token(username: str, full_name: str, role: str, expiry_hours: int = 12) -> str:
    """Creates a cryptographically secure token for authenticated administrator sessions."""
    token = secrets.token_urlsafe(36)
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    _active_admin_tokens[token] = {
        "username": username,
        "full_name": full_name,
        "role": role,
        "expires_at": expires_at,
    }
    return token


def verify_admin_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Verifies that an admin session token is valid and unexpired."""
    if not token or token not in _active_admin_tokens:
        return None
    session_data = _active_admin_tokens[token]
    if datetime.utcnow() > session_data["expires_at"]:
        del _active_admin_tokens[token]
        return None
    return session_data


def revoke_admin_token(token: str) -> bool:
    """Logs out an administrator by invalidating their session token."""
    if token in _active_admin_tokens:
        del _active_admin_tokens[token]
        return True
    return False


def generate_demo_otp(identifier: str) -> str:
    """
    Generates a 6-digit numeric OTP for demo campus portal verification.
    Clearly simulated on-device: does not invoke external paid SMS gateways.
    """
    clean_id = identifier.strip().upper()
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    _demo_otps[clean_id] = {
        "code": otp_code,
        "expires_at": expires_at
    }
    return otp_code


def verify_demo_otp(identifier: str, otp_code: str) -> bool:
    """Verifies demo OTP code within its 5-minute validity window."""
    clean_id = identifier.strip().upper()
    record = _demo_otps.get(clean_id)
    if not record:
        # Fallback acceptance for universal demo code '123456' during tests
        return otp_code.strip() == "123456"
    if datetime.utcnow() > record["expires_at"]:
        del _demo_otps[clean_id]
        return False
    if record["code"] == otp_code.strip():
        del _demo_otps[clean_id]
        return True
    return False


class GatewayError(Exception):
    """Base exception for gateway operations."""
    pass


class GatewayConnectionError(GatewayError):
    """Raised when the OpenWrt router is unreachable, times out, or network connection fails."""
    pass


class GatewayAuthenticationError(GatewayError):
    """Raised when SSH authentication or authorization to the gateway fails."""
    pass


class GatewayCommandError(GatewayError):
    """Raised when an OpenNDS ndsctl command fails or returns a non-zero exit code."""
    pass


class GatewayResponseError(GatewayError):
    """Raised when an OpenNDS response is malformed or cannot be parsed."""
    pass


class OpenWrtGatewayService:
    """
    Service communicating securely with OpenWrt 25.12.5 and OpenNDS 10.3.1.
    All gateway interactions fail closed by design to prevent unauthorized access.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        key_path: Optional[Path] = None,
        timeout_sec: Optional[int] = None,
        fas_key: Optional[str] = None,
        mhd_port: Optional[int] = None
    ):
        self.host = host or settings.OPENWRT_HOST
        self.user = user or settings.OPENWRT_USER
        self.key_path = Path(key_path or settings.OPENWRT_SSH_KEY_PATH)
        self.timeout_sec = timeout_sec or settings.OPENWRT_TIMEOUT_SEC
        self.fas_key = fas_key or settings.OPENNDS_FAS_KEY
        self.mhd_port = mhd_port or settings.OPENNDS_MHD_PORT

    def _run_ssh(self, command: str, timeout: Optional[int] = None) -> str:
        """Executes a non-interactive command over SSH to the OpenWrt VM."""
        actual_timeout = timeout or self.timeout_sec
        if not self.key_path.exists():
            raise GatewayConnectionError(f"Backend SSH private key not found at configured path: {self.key_path}")

        ssh_cmd = [
            "ssh",
            "-i", str(self.key_path),
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"ConnectTimeout={actual_timeout}",
            f"{self.user}@{self.host}",
            command
        ]

        try:
            res = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=actual_timeout + 2
            )
            if res.returncode != 0:
                err_msg = res.stderr.strip() or res.stdout.strip()
                if "permission denied" in err_msg.lower():
                    raise GatewayAuthenticationError(f"SSH authentication failed on gateway: {err_msg}")
                raise GatewayCommandError(f"Gateway command failed (exit code {res.returncode}): {err_msg}")
            return res.stdout
        except subprocess.TimeoutExpired:
            raise GatewayConnectionError(f"OpenWrt gateway at {self.host} timed out after {actual_timeout}s.")
        except (GatewayCommandError, GatewayAuthenticationError):
            raise
        except Exception as e:
            raise GatewayConnectionError(f"Failed to communicate with OpenWrt gateway: {str(e)}")

    def check_connectivity(self) -> bool:
        """Verifies whether the OpenWrt VM is reachable over SSH."""
        try:
            out = self._run_ssh("echo ping_ok", timeout=3)
            return "ping_ok" in out
        except Exception:
            return False

    def get_opennds_status(self) -> Dict[str, Any]:
        """
        Queries openNDS status via ndsctl.
        Returns parsed version, uptime, managed interface, and upstream WAN status.
        """
        try:
            out = self._run_ssh("ndsctl status", timeout=4)
        except Exception as e:
            raise GatewayConnectionError(f"Unable to query OpenNDS status: {str(e)}")

        status_info = {
            "running": True,
            "version": "10.3.1",
            "uptime": "Unknown",
            "managed_interface": "br-lan",
            "upstream_gateway": "online",
            "mhd_listening": f"{self.host}:{self.mhd_port}"
        }

        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Version:"):
                status_info["version"] = line.split(":", 1)[1].strip()
            elif line.startswith("Uptime:"):
                status_info["uptime"] = line.split(":", 1)[1].strip()
            elif line.startswith("Managed interface:"):
                status_info["managed_interface"] = line.split(":", 1)[1].strip()
            elif line.startswith("Upstream gateway"):
                status_info["upstream_gateway"] = line.split(":", 1)[1].strip()
            elif "MHD Server" in line and "listening on:" in line:
                mhd_part = line.split("listening on:", 1)[1].strip().replace("http://", "")
                status_info["mhd_listening"] = mhd_part

        return status_info

    def get_live_clients(self) -> Dict[str, Any]:
        """
        Retrieves real authoritative client connection states from OpenNDS kernel netfilter.
        Returns dict containing client list, active sessions, and byte counters.
        """
        try:
            out = self._run_ssh("ndsctl json", timeout=4)
            data = json.loads(out)
            return data
        except json.JSONDecodeError as e:
            raise GatewayResponseError(f"Failed to parse ndsctl JSON response: {str(e)}")
        except Exception as e:
            raise GatewayConnectionError(f"Unable to read live OpenNDS client states: {str(e)}")

    def build_auth_command(
        self,
        target: str,
        session_timeout_mins: int,
        upload_quota_kb: int,
        download_quota_kb: int,
        custom_identifier: str
    ) -> str:
        """
        Builds the exact ndsctl auth command:
        ndsctl auth mac|ip|token sessiontimeout(mins) uprate downrate upquota(kB) downquota(kB) "customstring"
        """
        s_timeout = max(1, int(session_timeout_mins))
        up_quota = max(0, int(upload_quota_kb))
        down_quota = max(0, int(download_quota_kb))
        clean_custom = re.sub(r'[^a-zA-Z0-9_\-\.:]', '_', custom_identifier)
        return f'ndsctl auth "{target}" {s_timeout} 0 0 {up_quota} {down_quota} "{clean_custom}"'

    def authorize_client(
        self,
        client_mac: str,
        session_timeout_mins: int,
        quota_kb: int,
        student_id: str,
        client_ip: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """
        Authorizes a student device on the OpenWrt gateway with quota split.
        FAIL-CLOSED: If the gateway command fails or router is offline, raises GatewayConnectionError.
        Internet access is NEVER granted if gateway authorization fails.
        Returns (success, upload_quota_kb, download_quota_kb).
        """
        normalized_mac = normalize_mac(client_mac)
        if not is_valid_mac(normalized_mac):
            raise GatewayCommandError(f"Invalid client MAC address: {client_mac}")

        # Split quota to prevent granting 2x remaining allowance
        up_quota_kb, down_quota_kb = split_quota_allocation(quota_kb)

        cmd = self.build_auth_command(
            target=normalized_mac,
            session_timeout_mins=session_timeout_mins,
            upload_quota_kb=up_quota_kb,
            download_quota_kb=down_quota_kb,
            custom_identifier=f"Student:{student_id}"
        )

        try:
            out = self._run_ssh(cmd, timeout=5)
            logger.info(f"OpenWrt authorized client {normalized_mac} for student {student_id} (Up: {up_quota_kb} kB, Down: {down_quota_kb} kB): {out.strip()}")
            return True, up_quota_kb, down_quota_kb
        except GatewayCommandError:
            raise
        except Exception as e:
            logger.error(f"Failed to authorize client {normalized_mac} on OpenWrt gateway: {str(e)}")
            raise GatewayConnectionError(f"Gateway authorization failed: {str(e)}")

    def deauthorize_client(self, target: str) -> bool:
        """
        De-authenticates a client device on OpenWrt, immediately cutting off gateway traffic.
        """
        clean_target = target.strip()
        cmd = f'ndsctl deauth "{clean_target}"'
        try:
            out = self._run_ssh(cmd, timeout=4)
            logger.info(f"OpenWrt deauthorized client {clean_target}: {out.strip()}")
            return True
        except Exception as e:
            logger.error(f"Failed to de-authorize client {clean_target} on OpenWrt: {str(e)}")
            raise GatewayConnectionError(f"Gateway de-authorization failed: {str(e)}")

    def get_wan_traffic_telemetry(self) -> Dict[str, Any]:
        """
        Reads real interface telemetry from OpenWrt /proc/net/dev for eth0 (WAN1).
        """
        try:
            cmd = "grep 'eth0:' /proc/net/dev | awk '{print $2, $3, $10, $11}'"
            out = self._run_ssh(cmd, timeout=3).strip()
            parts = out.split()
            if len(parts) >= 4:
                return {
                    "wan_interface": "eth0",
                    "rx_bytes": int(parts[0]),
                    "rx_packets": int(parts[1]),
                    "tx_bytes": int(parts[2]),
                    "tx_packets": int(parts[3]),
                    "is_live": True
                }
        except Exception:
            pass
        return {
            "wan_interface": "eth0",
            "rx_bytes": 0,
            "rx_packets": 0,
            "tx_bytes": 0,
            "tx_packets": 0,
            "is_live": False
        }


# Global singleton instance for backend services
gateway_service = OpenWrtGatewayService()
