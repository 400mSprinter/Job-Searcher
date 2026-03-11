# Created: 2026-03-11 11:00
from datetime import datetime
from db import get_connection

VALID_STATUSES = [
    "Applied",
    "Phone Screen",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
    "Ghosted",
]


def add_application(company, role, status="Applied", date_applied=None,
                    notes=None, url=None, contact=None, follow_up_date=None):
    if date_applied is None:
        date_applied = datetime.now().strftime("%Y-%m-%d")
    last_updated = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO applications
                (company, role, status, date_applied, last_updated, notes, url, contact, follow_up_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, status, date_applied, last_updated, notes, url, contact, follow_up_date),
        )
        conn.commit()
        return cursor.lastrowid


def update_application(id, **kwargs):
    kwargs["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [id]

    with get_connection() as conn:
        conn.execute(f"UPDATE applications SET {fields} WHERE id = ?", values)
        conn.commit()


def get_application(id):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM applications WHERE id = ?", (id,)).fetchone()


def list_applications(status=None):
    with get_connection() as conn:
        if status:
            return conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY date_applied DESC",
                (status,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM applications ORDER BY date_applied DESC"
        ).fetchall()


def delete_application(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (id,))
        conn.commit()
