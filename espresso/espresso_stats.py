# Created: 2026-04-02 10:00
from espresso.espresso_db import get_espresso_connection


def get_stats():
    with get_espresso_connection() as conn:
        totals = conn.execute("""
            SELECT
                COUNT(*) as total_shots,
                ROUND(AVG(brew_ratio), 2) as avg_ratio,
                ROUND(AVG(brew_time_secs), 1) as avg_brew_time,
                ROUND(AVG(rating), 1) as avg_rating,
                ROUND(AVG(dose_grams), 1) as avg_dose,
                ROUND(AVG(yield_grams), 1) as avg_yield
            FROM shots
        """).fetchone()

        rating_dist = conn.execute("""
            SELECT rating, COUNT(*) as count
            FROM shots WHERE rating IS NOT NULL
            GROUP BY rating ORDER BY rating
        """).fetchall()

        weekly = conn.execute("""
            SELECT
                strftime('%Y-%W', shot_date) as week,
                COUNT(*) as count,
                ROUND(AVG(rating), 1) as avg_rating
            FROM shots
            GROUP BY week
            ORDER BY week DESC
            LIMIT 8
        """).fetchall()

        top_beans = conn.execute("""
            SELECT bean_name, COUNT(*) as count, ROUND(AVG(rating), 1) as avg_rating
            FROM shots
            GROUP BY bean_name
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()

        best_shot = conn.execute("""
            SELECT * FROM shots WHERE rating IS NOT NULL
            ORDER BY rating DESC, shot_date DESC
            LIMIT 1
        """).fetchone()

        return {
            "totals": dict(totals) if totals else {},
            "rating_distribution": [dict(r) for r in rating_dist],
            "weekly_trend": [dict(w) for w in reversed(list(weekly))],
            "top_beans": [dict(b) for b in top_beans],
            "best_shot": dict(best_shot) if best_shot else None,
        }
