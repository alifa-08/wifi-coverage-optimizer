import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "backend" / "artifacts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "AI-Based Wi-Fi Coverage Optimization & Dead-Zone Prediction System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.environ.get("DATABASE_URL") or f"sqlite:///{DATA_DIR / 'wifi_optimizer.db'}"
    MODEL_PATH: str = str(MODELS_DIR / "random_forest_deadzone.joblib")

    # Environment & Application URLs
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")  # "development" | "production" | "testing"
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    # SMTP Email Configuration (Environment Variables Only)
    SMTP_ENABLED: bool = os.environ.get("SMTP_ENABLED", "false").lower() in ("true", "1", "yes")
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.environ.get("SMTP_FROM_EMAIL", "wifi-portal@campus.edu.in")
    SMTP_FROM_NAME: str = os.environ.get("SMTP_FROM_NAME", "Campus Wi-Fi Portal")
    SMTP_USE_TLS: bool = os.environ.get("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    # Security & Password Reset Policy
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15
    ALLOW_DEV_RESET_MAILBOX: bool = os.environ.get("ALLOW_DEV_RESET_MAILBOX", "true").lower() in ("true", "1", "yes")

    # OpenWrt & OpenNDS Gateway Integration (Backend-Private)
    OPENWRT_HOST: str = os.environ.get("OPENWRT_HOST") or os.environ.get("GATEWAY_HOST", "192.168.214.2")
    OPENWRT_USER: str = os.environ.get("OPENWRT_USER") or os.environ.get("GATEWAY_USER", "root")
    OPENWRT_SSH_KEY_PATH: str = os.environ.get("OPENWRT_SSH_KEY_PATH", str(Path.home() / ".ssh" / "id_ed25519"))
    OPENWRT_TIMEOUT_SEC: int = int(os.environ.get("OPENWRT_TIMEOUT_SEC", "5"))
    OPENNDS_FAS_KEY: str = os.environ.get("OPENNDS_FAS_KEY", "113def12f27fdd3fc8dbd31e8fe9c8079ab1295e0606b1764a25e4e7db50e8d4")
    OPENNDS_MHD_PORT: int = int(os.environ.get("OPENNDS_MHD_PORT", "2050"))

    # Campus floorplan dimensions (in meters)
    DEFAULT_BUILDING_WIDTH: float = 80.0
    DEFAULT_BUILDING_HEIGHT: float = 50.0

    # Wi-Fi Physical & RF defaults
    DEFAULT_TX_POWER_DBM: float = 20.0  # 100 mW
    REFERENCE_DISTANCE_M: float = 1.0
    PATH_LOSS_EXPONENT_LOS: float = 2.0
    PATH_LOSS_EXPONENT_NLOS: float = 3.2
    NOISE_FLOOR_DBM: float = -95.0

    # Dead zone thresholds
    RSSI_DEAD_ZONE_THRESHOLD: float = -78.0  # dBm below which signal is considered poor
    LATENCY_DEAD_ZONE_THRESHOLD: float = 120.0  # ms
    PACKET_LOSS_DEAD_ZONE_THRESHOLD: float = 15.0  # %
    THROUGHPUT_DEAD_ZONE_THRESHOLD: float = 5.0  # Mbps

settings = Settings()
