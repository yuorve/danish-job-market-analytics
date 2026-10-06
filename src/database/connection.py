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
    """Initialize schema if tables do not exist."""
    schema_file = schema_path or Path(__file__).parent / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
