"""
Database connection management for Danish Job Market Analytics.
Supports SQLite (local portfolio/demo) and hooks for PostgreSQL / Azure SQL.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path("data/processed/danish_jobs.db")

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return an active SQLite connection configured with Row factory and foreign keys."""
    target_path = Path(db_path or DEFAULT_DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database(db_path: Optional[Path] = None, schema_path: Optional[Path] = None) -> None:
    """Initialize schema if tables do not exist and ensure columns exist."""
    schema_file = schema_path or Path(__file__).parent / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)

        # Check and migrate columns if database already existed before new schema definitions
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(jobs)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        
        if "language_requirement" not in existing_cols and "jobs" in [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            cursor.execute("ALTER TABLE jobs ADD COLUMN language_requirement TEXT DEFAULT 'Unknown'")
            # Backfill existing jobs based on flags
            cursor.execute("""
                UPDATE jobs 
                SET language_requirement = CASE 
                    WHEN is_english_only = 1 THEN 'English'
                    WHEN is_danish_required = 1 THEN 'Danish'
                    ELSE 'Unknown'
                END
                WHERE language_requirement IS NULL OR language_requirement = 'Unknown';
            """)

        conn.commit()
