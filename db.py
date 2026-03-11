# Created: 2026-03-11 11:00
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'Applied',
                date_applied TEXT,
                last_updated TEXT,
                notes TEXT,
                url TEXT,
                contact TEXT,
                follow_up_date TEXT
            )
        """)
        conn.commit()
