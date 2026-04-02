# Created: 2026-04-02 10:00
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "espresso.db"


def get_espresso_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_espresso_db():
    with get_espresso_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                bean_name       TEXT NOT NULL,
                bean_origin     TEXT,
                bean_roaster    TEXT,
                roast_level     TEXT,
                dose_grams      REAL NOT NULL,
                yield_grams     REAL,
                brew_ratio      REAL,
                grind_size      INTEGER,
                grinder         TEXT,
                tamp_pressure   TEXT,
                brew_time_secs  INTEGER,
                water_temp_c    REAL,
                pressure_bar    REAL,
                machine         TEXT,
                pre_infusion    INTEGER DEFAULT 0,
                taste_notes     TEXT,
                rating          INTEGER,
                notes           TEXT,
                shot_date       TEXT NOT NULL,
                shot_time       TEXT,
                created_at      TEXT NOT NULL
            )
        """)
        conn.commit()
