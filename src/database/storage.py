"""Generic JSON persistence layer.

All file I/O for the app is funnelled through these two functions.
Callers receive a StorageError on any I/O or parse failure so that
app.py can surface a user-readable st.error() message.
"""

import json
from pathlib import Path
from typing import Any


class StorageError(Exception):
    """Raised when a JSON file cannot be read or written."""


def load_json(path: Path, default: Any) -> Any:
    """Load and return JSON data from *path*.

    Returns *default* if the file does not exist yet.
    Raises StorageError if the file exists but cannot be read or parsed.
    """
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(
            f"Failed to read '{path}': {exc}"
        ) from exc


def save_json(path: Path, data: Any) -> None:
    """Serialize *data* to JSON and write it to *path*.

    Creates parent directories if they do not exist.
    Raises StorageError on any write failure.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except (OSError, TypeError) as exc:
        raise StorageError(
            f"Failed to write '{path}': {exc}"
        ) from exc
