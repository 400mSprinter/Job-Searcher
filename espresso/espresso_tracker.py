# Created: 2026-04-02 10:00
from datetime import datetime

from espresso.espresso_db import get_espresso_connection


def add_shot(bean_name, dose_grams, bean_origin=None, bean_roaster=None,
             roast_level=None, yield_grams=None, grind_size=None, grinder=None,
             tamp_pressure=None, brew_time_secs=None, water_temp_c=None,
             pressure_bar=None, machine=None, pre_infusion=0, taste_notes=None,
             rating=None, notes=None, shot_date=None, shot_time=None):
    now = datetime.now()
    if shot_date is None:
        shot_date = now.strftime("%Y-%m-%d")
    if shot_time is None:
        shot_time = now.strftime("%H:%M")
    created_at = now.isoformat()

    brew_ratio = round(yield_grams / dose_grams, 2) if yield_grams and dose_grams else None

    with get_espresso_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO shots
                (bean_name, bean_origin, bean_roaster, roast_level,
                 dose_grams, yield_grams, brew_ratio, grind_size, grinder,
                 tamp_pressure, brew_time_secs, water_temp_c, pressure_bar,
                 machine, pre_infusion, taste_notes, rating, notes,
                 shot_date, shot_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bean_name, bean_origin, bean_roaster, roast_level,
              dose_grams, yield_grams, brew_ratio, grind_size, grinder,
              tamp_pressure, brew_time_secs, water_temp_c, pressure_bar,
              machine, pre_infusion, taste_notes, rating, notes,
              shot_date, shot_time, created_at))
        conn.commit()
        return cursor.lastrowid


def update_shot(id, **kwargs):
    if "yield_grams" in kwargs or "dose_grams" in kwargs:
        with get_espresso_connection() as conn:
            row = conn.execute("SELECT dose_grams, yield_grams FROM shots WHERE id = ?", (id,)).fetchone()
            if row:
                dose = kwargs.get("dose_grams", row["dose_grams"])
                yld = kwargs.get("yield_grams", row["yield_grams"])
                if dose and yld:
                    kwargs["brew_ratio"] = round(yld / dose, 2)

    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [id]

    with get_espresso_connection() as conn:
        conn.execute(f"UPDATE shots SET {fields} WHERE id = ?", values)
        conn.commit()


def get_shot(id):
    with get_espresso_connection() as conn:
        return conn.execute("SELECT * FROM shots WHERE id = ?", (id,)).fetchone()


def list_shots(days=None, bean=None, rating=None):
    conditions = []
    params = []

    if days:
        conditions.append("shot_date >= date('now', ?)")
        params.append(f"-{days} days")
    if bean:
        conditions.append("bean_name LIKE ?")
        params.append(f"%{bean}%")
    if rating:
        conditions.append("rating >= ?")
        params.append(rating)

    where = " AND ".join(conditions)
    query = "SELECT * FROM shots"
    if where:
        query += f" WHERE {where}"
    query += " ORDER BY shot_date DESC, shot_time DESC"

    with get_espresso_connection() as conn:
        return conn.execute(query, params).fetchall()


def delete_shot(id):
    with get_espresso_connection() as conn:
        conn.execute("DELETE FROM shots WHERE id = ?", (id,))
        conn.commit()


def get_distinct_beans():
    with get_espresso_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT bean_name FROM shots ORDER BY bean_name"
        ).fetchall()
        return [r["bean_name"] for r in rows]


def get_distinct_equipment():
    with get_espresso_connection() as conn:
        grinders = conn.execute(
            "SELECT DISTINCT grinder FROM shots WHERE grinder IS NOT NULL ORDER BY grinder"
        ).fetchall()
        machines = conn.execute(
            "SELECT DISTINCT machine FROM shots WHERE machine IS NOT NULL ORDER BY machine"
        ).fetchall()
        return {
            "grinders": [r["grinder"] for r in grinders],
            "machines": [r["machine"] for r in machines],
        }
