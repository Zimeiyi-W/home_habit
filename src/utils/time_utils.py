"""Timezone-aware date and time helpers.

Single source of truth for all time operations in the app.
All functions default to America/Los_Angeles but accept any pytz-valid tz_name.
"""

from datetime import date, datetime, timedelta

import pytz


def get_local_now(tz_name: str = "America/Los_Angeles") -> datetime:
    """Return the current datetime in the specified timezone."""
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)


def get_today(tz_name: str = "America/Los_Angeles") -> date:
    """Return today's date in the specified timezone."""
    return get_local_now(tz_name).date()


def get_day_name(tz_name: str = "America/Los_Angeles") -> str:
    """Return the full weekday name (e.g. 'Monday') for today in the specified timezone."""
    return get_today(tz_name).strftime("%A")


def get_week_start(tz_name: str = "America/Los_Angeles") -> date:
    """Return the most recent Monday as a date object in the specified timezone."""
    today = get_today(tz_name)
    return today - timedelta(days=today.weekday())


def days_until(target: date, tz_name: str = "America/Los_Angeles") -> int:
    """Return (target - today).days; negative if the date is in the past."""
    return (target - get_today(tz_name)).days
