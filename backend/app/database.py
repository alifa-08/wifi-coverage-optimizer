from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings, DATA_DIR

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema_migrations():
    """Ensure newly added columns and gateway tables exist in SQLite database."""
    import sqlite3
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    else:
        db_path = DATA_DIR / "wifi_optimizer.db"
    if not db_path.exists():
        return
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(simulation_runs)")
        cols = [row[1] for row in cur.fetchall()]
        if cols and "is_synthetic" not in cols:
            cur.execute("ALTER TABLE simulation_runs ADD COLUMN is_synthetic BOOLEAN DEFAULT 1")

        cur.execute("PRAGMA table_info(measurements)")
        m_cols = [row[1] for row in cur.fetchall()]
        if m_cols and "is_synthetic" not in m_cols:
            cur.execute("ALTER TABLE measurements ADD COLUMN is_synthetic BOOLEAN DEFAULT 1")

        # Gateway migrations: students table
        cur.execute("PRAGMA table_info(students)")
        s_cols = [row[1] for row in cur.fetchall()]
        if s_cols:
            if "college_usn" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN college_usn VARCHAR(50)")
                # Update demo accounts with default USNs
                cur.execute("UPDATE students SET college_usn = 'DEMO-USN-CSE01' WHERE student_id = 'DEMO-CSE-01'")
                cur.execute("UPDATE students SET college_usn = 'DEMO-USN-IT02' WHERE student_id = 'DEMO-IT-02'")
                cur.execute("UPDATE students SET college_usn = 'DEMO-USN-ECE03' WHERE student_id = 'DEMO-ECE-03'")
                cur.execute("UPDATE students SET college_usn = 'DEMO-USN-ME04' WHERE student_id = 'DEMO-MECH-04'")
                cur.execute("UPDATE students SET college_usn = 'DEMO-USN-EXH05' WHERE student_id = 'DEMO-EXHAUSTED'")
            if "academic_year" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN academic_year VARCHAR(20) DEFAULT '3rd Year'")
            if "batch_year" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN batch_year INTEGER DEFAULT 2023")
            if "department_code" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN department_code VARCHAR(10) DEFAULT 'CS'")
            if "approval_status" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN approval_status VARCHAR(30) DEFAULT 'APPROVED'")
            if "is_demo" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN is_demo BOOLEAN DEFAULT 0")
                cur.execute("UPDATE students SET is_demo = 1 WHERE college_usn LIKE 'DEMO%' OR student_id LIKE 'DEMO%'")
            if "email" not in s_cols:
                cur.execute("ALTER TABLE students ADD COLUMN email VARCHAR(120)")
                # Seed default demo student emails
                cur.execute("UPDATE students SET email = 'demo.cse01@campus.edu.in' WHERE student_id = 'DEMO-CSE-01'")
                cur.execute("UPDATE students SET email = 'demo.it02@campus.edu.in' WHERE student_id = 'DEMO-IT-02'")
                cur.execute("UPDATE students SET email = 'demo.ece03@campus.edu.in' WHERE student_id = 'DEMO-ECE-03'")
                cur.execute("UPDATE students SET email = 'demo.mech04@campus.edu.in' WHERE student_id = 'DEMO-MECH-04'")
                cur.execute("UPDATE students SET email = 'demo.exhausted@campus.edu.in' WHERE student_id = 'DEMO-EXHAUSTED'")
                cur.execute("UPDATE students SET email = 'alia.eng23cs0000@campus.edu.in' WHERE college_usn = 'ENG23CS0000'")

        # Ensure password_reset_tokens table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_tokens'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    created_at DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used_at DATETIME,
                    is_invalidated BOOLEAN NOT NULL DEFAULT 0,
                    ip_address VARCHAR(50),
                    user_agent VARCHAR(255),
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_student_id ON password_reset_tokens(student_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens(expires_at)")

        conn.commit()
        conn.close()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
