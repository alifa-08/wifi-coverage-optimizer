import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional, Any

from app.config import settings

logger = logging.getLogger(__name__)

# ==============================================================================
# Development Mailbox (Available ONLY in development / testing environments)
# ==============================================================================
_dev_mailbox: List[Dict[str, Any]] = []
_dev_mailbox_lock = threading.Lock()


def is_dev_mailbox_enabled() -> bool:
    """
    Fail-secure check for development mailbox:
    1. Returns False if ENVIRONMENT is missing, empty, or whitespace.
    2. Strictly disabled if ENVIRONMENT contains 'prod', 'production', or 'live'.
    3. Strictly disabled if ENVIRONMENT is not explicitly 'development' or 'testing'.
    4. Strictly disabled unless ALLOW_DEV_RESET_MAILBOX is explicitly enabled.
    """
    raw_env = (getattr(settings, "ENVIRONMENT", None) or "").strip().lower()
    if not raw_env:
        return False
    if any(keyword in raw_env for keyword in ("prod", "production", "live")):
        return False
    if raw_env not in ("development", "testing", "test", "dev"):
        return False
    return bool(getattr(settings, "ALLOW_DEV_RESET_MAILBOX", False))


def get_dev_mailbox() -> List[Dict[str, Any]]:
    """
    Returns dispatched reset messages captured during development or testing.
    Strictly restricted: always returns an empty list in production or when disabled.
    """
    if not is_dev_mailbox_enabled():
        return []
    with _dev_mailbox_lock:
        return list(_dev_mailbox)


def clear_dev_mailbox() -> None:
    """Clears development mailbox items (used between test runs)."""
    with _dev_mailbox_lock:
        _dev_mailbox.clear()


# ==============================================================================
# In-Memory Sliding-Window Rate Limiter
# ==============================================================================
_rate_limit_store: Dict[str, List[datetime]] = {}
_rate_limit_lock = threading.Lock()


def check_rate_limit(key: str, max_requests: int = 5, window_seconds: int = 900) -> bool:
    """
    Sliding window rate limiter:
    Returns True if the request is permitted, or False if the rate limit is exceeded.
    Automatically prunes expired entries to prevent memory growth.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    with _rate_limit_lock:
        timestamps = _rate_limit_store.get(key, [])
        # Prune timestamps older than window
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= max_requests:
            _rate_limit_store[key] = valid_timestamps
            return False

        valid_timestamps.append(now)
        _rate_limit_store[key] = valid_timestamps

        # Periodic cleanup of completely stale keys if store grows large
        if len(_rate_limit_store) > 1000:
            stale_threshold = now - timedelta(seconds=window_seconds * 2)
            keys_to_remove = [
                k for k, ts in _rate_limit_store.items()
                if not ts or max(ts) < stale_threshold
            ]
            for k in keys_to_remove:
                del _rate_limit_store[k]

        return True


def clear_rate_limits() -> None:
    """Resets rate limit counters (useful for automated test isolation)."""
    with _rate_limit_lock:
        _rate_limit_store.clear()


# ==============================================================================
# Email Dispatcher
# ==============================================================================
def send_password_reset_email(
    to_email: str,
    recipient_name: str,
    college_usn: str,
    raw_token: str
) -> Tuple[bool, str]:
    """
    Dispatches a single-use password reset link to the student's registered email.

    Security rules enforced:
    1. Raw reset token is NEVER logged to logs or terminal.
    2. Reset link points to frontend URL configured via environment.
    3. If SMTP is not configured or disabled, does NOT claim an email was sent.
    4. In development/testing mode, captures token in dev mailbox for verification.

    Returns:
        (success: bool, status_message: str)
    """
    reset_url = f"{settings.FRONTEND_URL}/?view=reset-password&token={raw_token}"

    # Capture in development mailbox if enabled and in non-production environment
    if is_dev_mailbox_enabled():
        with _dev_mailbox_lock:
            _dev_mailbox.append({
                "to_email": to_email,
                "recipient_name": recipient_name,
                "college_usn": college_usn,
                "reset_url": reset_url,
                "raw_token": raw_token,
                "timestamp": datetime.utcnow()
            })
            # Bound development mailbox to last 50 items
            if len(_dev_mailbox) > 50:
                _dev_mailbox.pop(0)

    # Check if live SMTP delivery is configured
    if not settings.SMTP_ENABLED or not settings.SMTP_HOST.strip():
        logger.info(
            "SMTP email delivery is disabled or unconfigured (SMTP_ENABLED=%s). "
            "Password reset link generated for student USN: %s.",
            settings.SMTP_ENABLED,
            college_usn
        )
        return False, "SMTP email delivery is currently disabled or unconfigured on this campus server."

    # Compose MIME email message
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Campus Wi-Fi Portal - Password Reset Request"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        plain_text = f"""Hello {recipient_name},

A password reset was requested for your campus Wi-Fi account (USN: {college_usn}).

To reset your password, open the following link in your browser:
{reset_url}

This link is valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes and can only be used once.

If you did not make this request, you can safely ignore this email; your current password remains unchanged.

Regards,
Campus Network Administration
"""

        html_text = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; padding: 24px;">
  <div style="max-width: 540px; margin: 0 auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 28px;">
    <h2 style="color: #38bdf8; margin-top: 0;">Campus Wi-Fi Access</h2>
    <p>Hello <strong>{recipient_name}</strong>,</p>
    <p>A password reset was requested for your student account (USN: <code style="color: #a5f3fc; background: #082f49; padding: 2px 6px; border-radius: 4px;">{college_usn}</code>).</p>
    <p style="margin: 24px 0;">
      <a href="{reset_url}" style="background-color: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
        Reset My Password
      </a>
    </p>
    <p style="font-size: 12px; color: #94a3b8;">
      This single-use link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes. If you did not request this, please disregard this email.
    </p>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_text, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Successfully delivered password reset email to %s for student %s.", to_email, college_usn)
        return True, "Password reset email delivered successfully."

    except Exception as e:
        logger.error("Failed to deliver password reset email to %s: %s", to_email, str(e))
        return False, f"SMTP delivery error: {str(e)}"
