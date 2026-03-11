# Created: 2026-03-11 11:00
from datetime import datetime
from tracker import list_applications

# Days after last update before a follow-up is suggested, per status
FOLLOW_UP_DAYS = {
    "Applied": 7,
    "Phone Screen": 5,
    "Interview": 3,
    "Ghosted": 14,
}

TERMINAL_STATUSES = {"Offer", "Rejected", "Withdrawn"}


def get_reminders():
    """Return list of (application, reason) tuples that need follow-up."""
    apps = list_applications()
    today = datetime.now().date()
    reminders = []

    for app in apps:
        if app["status"] in TERMINAL_STATUSES:
            continue

        # Check explicit follow-up date first
        if app["follow_up_date"]:
            follow_up = datetime.strptime(app["follow_up_date"], "%Y-%m-%d").date()
            if follow_up <= today:
                days_overdue = (today - follow_up).days
                label = "today" if days_overdue == 0 else f"{days_overdue}d overdue"
                reminders.append((app, f"Follow-up date reached ({label})"))
            continue

        # Fall back to status-based threshold
        threshold = FOLLOW_UP_DAYS.get(app["status"])
        if threshold and app["last_updated"]:
            last = datetime.strptime(app["last_updated"], "%Y-%m-%d").date()
            days_elapsed = (today - last).days
            if days_elapsed >= threshold:
                reminders.append((
                    app,
                    f"{days_elapsed}d since last update (follow up after {threshold}d)",
                ))

    return reminders
