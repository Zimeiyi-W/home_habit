"""Cleaning schedule and weekly record management.

No Streamlit imports — pure business logic only.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from src.database.storage import load_json, save_json

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_SCHEDULE: dict[str, list[str]] = {
    "Monday":    ["Vacuum Floors", "Wipe Kitchen Counters", "Empty Trash"],
    "Tuesday":   ["Scrub Toilets", "Clean Mirrors", "Sink Scrub"],
    "Wednesday": ["Dust Electronics", "Dust Shelves"],
    "Thursday":  ["Vacuum Floors", "Organize Clothes"],
    "Friday":    ["Organize Pantry"],
    "Saturday":  ["Clean Stove", "Clean Yards"],
    "Sunday":    ["Vacuum Floors", "Laundry - Wash & Fold"],
}

ORDERED_DAYS: list[str] = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

# ── Schedule CRUD ──────────────────────────────────────────────────────────────


def load_schedule(path: Path) -> dict[str, list[str]]:
    """Load the weekly schedule from *path*, seeding defaults if missing."""
    data: Any = load_json(path, default=None)
    if data is None:
        save_schedule(path, DEFAULT_SCHEDULE)
        return dict(DEFAULT_SCHEDULE)
    return data


def save_schedule(path: Path, schedule: dict[str, list[str]]) -> None:
    """Persist the weekly schedule to *path*."""
    save_json(path, schedule)


def add_task(schedule: dict[str, list[str]], day: str, task: str) -> dict[str, list[str]]:
    """Return a new schedule with *task* appended to *day*.

    Raises ValueError if *day* is not in the schedule or *task* is blank.
    """
    if day not in schedule:
        raise ValueError(f"Day '{day}' not found in schedule.")
    task = task.strip()
    if not task:
        raise ValueError("Task name cannot be blank.")
    updated = {d: list(tasks) for d, tasks in schedule.items()}
    updated[day].append(task)
    return updated


def remove_task(schedule: dict[str, list[str]], day: str, index: int) -> dict[str, list[str]]:
    """Return a new schedule with the task at *index* removed from *day*.

    Raises ValueError for an out-of-range index or unknown day.
    """
    if day not in schedule:
        raise ValueError(f"Day '{day}' not found in schedule.")
    tasks = list(schedule[day])
    if not (0 <= index < len(tasks)):
        raise ValueError(f"Index {index} is out of range for day '{day}'.")
    tasks.pop(index)
    updated = {d: list(t) for d, t in schedule.items()}
    updated[day] = tasks
    return updated


def add_day(schedule: dict[str, list[str]], day: str) -> dict[str, list[str]]:
    """Return a new schedule with an empty entry for *day*.

    Raises ValueError if *day* already exists.
    """
    day = day.strip()
    if not day:
        raise ValueError("Day name cannot be blank.")
    if day in schedule:
        raise ValueError(f"Day '{day}' already exists in schedule.")
    updated = {d: list(tasks) for d, tasks in schedule.items()}
    updated[day] = []
    return updated


# ── Weekly Record ──────────────────────────────────────────────────────────────


def load_weekly_record(path: Path, week_start: date) -> dict[str, dict[str, bool]]:
    """Load this week's task-completion record.

    If the stored week_start differs from the current *week_start* (new week),
    returns a fresh empty dict so the app starts clean without a cron job.
    """
    raw: Any = load_json(path, default=None)
    if raw is None:
        return {}
    stored_week_start = raw.get("week_start")
    if stored_week_start != week_start.isoformat():
        return {}
    return raw.get("records", {})


def save_weekly_record(
    path: Path, week_start: date, records: dict[str, dict[str, bool]]
) -> None:
    """Write the week's completion records with its ISO week_start key."""
    save_json(path, {"week_start": week_start.isoformat(), "records": records})


# ── Missed Task Logic ──────────────────────────────────────────────────────────


def get_missed_tasks(
    schedule: dict[str, list[str]],
    records: dict[str, dict[str, bool]],
    past_days: list[str],
) -> dict[str, list[str]]:
    """Return {day: [missed_task, ...]} for each past day in the current week.

    A task is "missed" if it appears in the schedule for that day but was not
    marked True in *records*.
    """
    missed: dict[str, list[str]] = {}
    for day in past_days:
        day_tasks = schedule.get(day, [])
        day_record = records.get(day, {})
        missed_for_day = [t for t in day_tasks if not day_record.get(t, False)]
        if missed_for_day:
            missed[day] = missed_for_day
    return missed
