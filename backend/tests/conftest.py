"""
Pytest configuration and session fixtures.
Guarantees 100% production database safety: spins up an isolated, temporary SQLite
database snapshot for all tests, completely protecting data/wifi_optimizer.db.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Spin up an isolated temporary database BEFORE any test collection / imports occur
_prod_db = Path("data/wifi_optimizer.db").resolve()
_temp_dir = tempfile.mkdtemp(prefix="pytest_isolated_db_")
_temp_db_path = Path(_temp_dir) / "test_wifi_optimizer.db"

if _prod_db.exists():
    shutil.copyfile(_prod_db, _temp_db_path)

os.environ["DATABASE_URL"] = f"sqlite:///{_temp_db_path.resolve()}"

@pytest.fixture(scope="session", autouse=True)
def isolated_database_session():
    """Ensure all tests run against the isolated database snapshot."""
    yield _temp_db_path

    # Teardown connection pool and purge temporary database directory
    try:
        from app.database import engine
        engine.dispose()
    except Exception:
        pass
    try:
        shutil.rmtree(_temp_dir, ignore_errors=True)
    except Exception:
        pass
