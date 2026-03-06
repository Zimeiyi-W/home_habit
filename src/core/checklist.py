"""Go-out scenario checklist management.

No Streamlit imports — pure business logic only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.database.storage import load_json, save_json

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_SCENARIOS: dict[str, list[str]] = {
    "Shopping alone":    ["Driver's license", "Lock front door", "Wallet", "Phone"],
    "Library with kid":  ["Black bag (diapers, wipes, bottles, milk)", "Wallet", "Phone"],
    "Roadtrip with kid": ["Black bag", "Blue bag (food & utensils)", "Stroller", "Luna's hat", "Wallet", "Driver's license", "Phone"],
    "Work":              ["ID badge", "Laptop", "Charger", "Phone"],
}

# ── CRUD ──────────────────────────────────────────────────────────────────────


def load_scenarios(path: Path) -> dict[str, list[str]]:
    """Load scenarios from *path*, seeding defaults if the file is missing."""
    data: Any = load_json(path, default=None)
    if data is None:
        save_scenarios(path, DEFAULT_SCENARIOS)
        return dict(DEFAULT_SCENARIOS)
    return data


def save_scenarios(path: Path, scenarios: dict[str, list[str]]) -> None:
    """Persist *scenarios* to *path*."""
    save_json(path, scenarios)


def add_scenario(scenarios: dict[str, list[str]], name: str) -> dict[str, list[str]]:
    """Return a new dict with an empty scenario called *name*.

    Raises ValueError if *name* is blank or already exists.
    """
    name = name.strip()
    if not name:
        raise ValueError("Scenario name cannot be blank.")
    if name in scenarios:
        raise ValueError(f"Scenario '{name}' already exists.")
    updated = {k: list(v) for k, v in scenarios.items()}
    updated[name] = []
    return updated


def remove_scenario(scenarios: dict[str, list[str]], name: str) -> dict[str, list[str]]:
    """Return a new dict without the scenario called *name*.

    Raises ValueError if *name* does not exist.
    """
    if name not in scenarios:
        raise ValueError(f"Scenario '{name}' not found.")
    return {k: list(v) for k, v in scenarios.items() if k != name}


def add_item(scenarios: dict[str, list[str]], scenario: str, item: str) -> dict[str, list[str]]:
    """Return a new dict with *item* appended to *scenario*'s list.

    Raises ValueError if *scenario* is unknown or *item* is blank.
    """
    if scenario not in scenarios:
        raise ValueError(f"Scenario '{scenario}' not found.")
    item = item.strip()
    if not item:
        raise ValueError("Item name cannot be blank.")
    updated = {k: list(v) for k, v in scenarios.items()}
    updated[scenario].append(item)
    return updated


def remove_item(scenarios: dict[str, list[str]], scenario: str, index: int) -> dict[str, list[str]]:
    """Return a new dict with the item at *index* removed from *scenario*.

    Raises ValueError for an unknown scenario or out-of-range index.
    """
    if scenario not in scenarios:
        raise ValueError(f"Scenario '{scenario}' not found.")
    items = list(scenarios[scenario])
    if not (0 <= index < len(items)):
        raise ValueError(f"Index {index} is out of range for scenario '{scenario}'.")
    items.pop(index)
    updated = {k: list(v) for k, v in scenarios.items()}
    updated[scenario] = items
    return updated
