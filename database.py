"""
Database layer for AquaForensics using SQLite.
Handles table initialization and lightweight SQLite context connection management.
"""
import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(os.getenv("AQUAFORENSICS_DB_PATH", Path(__file__).parent / "aquaforensics.db"))

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Investigations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                initial_description TEXT,
                observer_reliability REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        
        # Observations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                action_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reliability REAL NOT NULL,
                source_class TEXT NOT NULL,
                claimed_source TEXT NOT NULL,
                notes TEXT,
                timestamp_min REAL,
                observed_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
            );
        """)
        
        # Assessments table (Auditable timeline snapshot)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                config_version TEXT NOT NULL,
                input_snapshot TEXT NOT NULL,
                output_snapshot TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
            );
        """)
        
        # ActionRecords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_records (
                id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                action_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                observation_id TEXT,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
                FOREIGN KEY (observation_id) REFERENCES observations(id) ON DELETE SET NULL
            );
        """)
