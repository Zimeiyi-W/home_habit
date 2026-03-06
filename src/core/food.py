"""Food inventory management, expiry checks, and category sorting.

No Streamlit imports — pure business logic only.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from src.database.storage import load_json, save_json
from src.utils.time_utils import days_until

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_LEVELS: tuple[str, ...] = ("High", "Medium", "Low")
VALID_CATEGORIES: tuple[str, ...] = ("Fresh Produce", "Longer Shelf Life")
EXPIRY_WARNING_DAYS: int = 7

LEVEL_STYLE: dict[str, dict[str, str]] = {
    "High":   {"emoji": "🟢", "bg": "#d4edda", "fg": "#155724"},
    "Medium": {"emoji": "🟡", "bg": "#fff3cd", "fg": "#856404"},
    "Low":    {"emoji": "🔴", "bg": "#f8d7da", "fg": "#721c24"},
}

_CATEGORY_ORDER: dict[str, int] = {cat: i for i, cat in enumerate(VALID_CATEGORIES)}

# ── Persistence ───────────────────────────────────────────────────────────────


def load_food(path: Path) -> list[dict]:
    """Load food inventory from *path*, seeding an empty list if missing."""
    data: Any = load_json(path, default=None)
    if data is None:
        save_food(path, [])
        return []
    return data


def save_food(path: Path, items: list[dict]) -> None:
    """Persist *items* to *path*."""
    save_json(path, items)


# ── CRUD ──────────────────────────────────────────────────────────────────────


def add_item(
    items: list[dict],
    name: str,
    category: str,
    level: str,
    expiry_date: date,
) -> list[dict]:
    """Return a new list with the given item appended.

    Raises ValueError for blank name, invalid category, or invalid level.
    """
    name = name.strip()
    if not name:
        raise ValueError("Item name cannot be blank.")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Category must be one of {VALID_CATEGORIES}.")
    if level not in VALID_LEVELS:
        raise ValueError(f"Level must be one of {VALID_LEVELS}.")

    new_item: dict = {
        "name": name,
        "category": category,
        "level": level,
        "expiry_date": expiry_date.isoformat(),
    }
    return list(items) + [new_item]


def remove_item(items: list[dict], index: int) -> list[dict]:
    """Return a new list with the item at *index* removed.

    Raises ValueError for an out-of-range index.
    """
    if not (0 <= index < len(items)):
        raise ValueError(f"Index {index} is out of range.")
    updated = list(items)
    updated.pop(index)
    return updated


def update_item(items: list[dict], index: int, level: str) -> list[dict]:
    """Return a new list with the level of the item at *index* updated.

    Raises ValueError for an out-of-range index or invalid level.
    """
    if not (0 <= index < len(items)):
        raise ValueError(f"Index {index} is out of range.")
    if level not in VALID_LEVELS:
        raise ValueError(f"Level must be one of {VALID_LEVELS}.")
    updated = list(items)
    updated[index] = {**updated[index], "level": level}
    return updated


# ── Sorting & expiry ──────────────────────────────────────────────────────────


def sort_items(items: list[dict]) -> list[dict]:
    """Return items sorted by category order, then by expiry_date ascending."""
    return sorted(
        items,
        key=lambda it: (
            _CATEGORY_ORDER.get(it.get("category", ""), 99),
            it.get("expiry_date", ""),
        ),
    )


def is_expiring_soon(expiry_date_str: str, today: date) -> bool:
    """Return True if the item expires within EXPIRY_WARNING_DAYS days."""
    try:
        target = date.fromisoformat(expiry_date_str)
    except ValueError:
        return False
    return days_until(target) <= EXPIRY_WARNING_DAYS
