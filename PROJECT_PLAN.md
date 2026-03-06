# Home Analytics Platform — Project Plan

**Author:** Meiyi (eng-assisted)
**Status:** Pre-implementation
**Last updated:** 2026-03-05 (session 4)

---

## 1. Project Overview

Transform a single-file Streamlit habit tracker into a modular, mobile-friendly personal home analytics platform. The app will be structured for long-term maintainability following the standards defined in `CLAUDE.md`.

### Goals
- Multi-tab web app accessible from a phone browser on local WiFi
- Clean separation between UI, business logic, and storage
- All data persisted in local JSON files (no external database)
- Editable content (schedules, scenarios, food list) managed from within the app

### Out of Scope (v1)
- User authentication
- Push notifications / background reminders
- Cloud hosting (local network only for now)

---

## 2. Feature Scope

| Tab | Feature | Persistence |
|---|---|---|
| 🏠 Cleaning | Daily task checklist | `data/weekly_record.json` (current week only) |
| 🏠 Cleaning | "Missed this week" reminder panel | Derived from `weekly_record.json` |
| 🏠 Cleaning | Editable weekly schedule | `data/cleaning_schedule.json` |
| 🎒 Go-Out Checklist | Scenario-based checklists (stateless) | None |
| 🎒 Go-Out Checklist | Editable scenarios & items | `data/scenarios.json` |
| 🥦 Food Inventory | Running list with category, volume level, and expiry date | `data/food_inventory.json` |
| 🥦 Food Inventory | Expiry warning (≤7 days → red) | Computed from expiry date at runtime |
| 🥦 Food Inventory | Fresh Produce shown above Longer Shelf Life | Sorted at render time |

---

## 3. Directory Structure

Following the standard defined in `CLAUDE.md`:

```
home-analytics/
│
├── app.py                        # Entry point — layout and tab routing only
│
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cleaning.py           # Schedule logic, score calc, weekly record management
│   │   ├── checklist.py          # Go-out scenario logic
│   │   └── food.py               # Food inventory logic, expiry checks, category sorting
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── storage.py            # Generic JSON read/write with error handling
│   │
│   └── utils/
│       ├── __init__.py
│       └── time_utils.py         # Timezone-aware date/time helpers
│
├── data/                         # Runtime data (git-ignored)
│   ├── cleaning_schedule.json    # Weekly task definitions
│   ├── weekly_record.json        # Current week's task completion (resets Mondays)
│   ├── scenarios.json            # Go-out checklist scenarios
│   └── food_inventory.json       # Current pantry list
│
├── assets/                       # Static assets (CSS, images)
│
├── .env                          # File paths and config (git-ignored)
├── .gitignore
└── requirements.txt
```

---

## 4. Data Schemas

### `data/cleaning_schedule.json`
```json
{
  "Monday":    ["Vacuum Floors", "Wipe Kitchen Counters", "Empty Trash"],
  "Tuesday":   ["Scrub Toilets", "Clean Mirrors", "Sink Scrub"],
  "Wednesday": ["Dust Electronics", "Dust Shelves"],
  "Thursday":  ["Vacuum Floors", "Organize Clothes"],
  "Friday":    ["Organize Pantry"],
  "Saturday":  ["Clean Stove", "Clean Yards"],
  "Sunday":    ["Vacuum Floors", "Laundry - Wash & Fold"]
}
```

### `data/weekly_record.json`
Stores the current ISO week's task completion. Auto-resets every Monday.
```json
{
  "week_start": "2026-03-02",
  "records": {
    "Monday":    {"Vacuum Floors": true,  "Wipe Kitchen Counters": false},
    "Tuesday":   {"Scrub Toilets": true,  "Clean Mirrors": false},
    "Wednesday": {}
  }
}
```
- `week_start`: ISO date string of the most recent Monday
- `records`: only past days are stored (today's checkboxes are live, not pre-loaded from here)
- On save: merge today's form result into `records[day_name]` and write file

### `data/scenarios.json`
```json
{
  "Shopping alone":    ["Driver's license", "Lock front door", "Wallet", "Phone"],
  "Library with kid":  ["Black bag (diapers, wipes...)", "Library card", "Phone"],
  "Roadtrip with kid": ["Black bag", "Blue bag (food & utensils)", "Stroller", "Driver's license"],
  "Work":              ["ID badge", "Laptop", "Charger", "Phone"]
}
```

### `data/food_inventory.json`
```json
[
  {"name": "Spinach",  "category": "Fresh Produce",      "level": "Low",    "expiry_date": "2026-03-08"},
  {"name": "Milk",     "category": "Fresh Produce",      "level": "High",   "expiry_date": "2026-03-12"},
  {"name": "Rice",     "category": "Longer Shelf Life",  "level": "High",   "expiry_date": "2027-06-01"},
  {"name": "Canned Beans", "category": "Longer Shelf Life", "level": "Medium", "expiry_date": "2027-01-15"}
]
```
- `category`: one of `"Fresh Produce"` or `"Longer Shelf Life"`
- `level`: one of `"High"`, `"Medium"`, `"Low"` (volume/stock level)
- `expiry_date`: ISO 8601 format (`YYYY-MM-DD`)
- Items are sorted at render time: Fresh Produce first, then Longer Shelf Life; within each group, sorted by `expiry_date` ascending

---

## 5. Module Responsibilities

### `src/utils/time_utils.py`
Single source of truth for timezone-aware date and time.

```python
def get_local_now(tz_name: str = "America/Los_Angeles") -> datetime
def get_today(tz_name: str = "America/Los_Angeles") -> date
def get_day_name(tz_name: str = "America/Los_Angeles") -> str
def get_week_start(tz_name: str = "America/Los_Angeles") -> date
    # Returns the most recent Monday as a date object
def days_until(target: date) -> int
    # Returns (target - today).days; negative if past
```

### `src/database/storage.py`
Generic, reusable JSON persistence layer. All file I/O goes here.

```python
class StorageError(Exception): ...

def load_json(path: Path, default: Any) -> Any
    # Returns `default` if file missing
    # Raises StorageError on corrupt/unreadable data

def save_json(path: Path, data: Any) -> None
    # Raises StorageError on write failure
    # Never swallows exceptions silently
```

### `src/core/cleaning.py`
Schedule management and weekly record tracking. No Streamlit imports.

```python
DEFAULT_SCHEDULE: dict[str, list[str]]

def load_schedule(path: Path) -> dict[str, list[str]]
def save_schedule(path: Path, schedule: dict[str, list[str]]) -> None
def add_task(schedule: dict, day: str, task: str) -> dict[str, list[str]]
def remove_task(schedule: dict, day: str, index: int) -> dict[str, list[str]]
def add_day(schedule: dict, day: str) -> dict[str, list[str]]

def load_weekly_record(path: Path, week_start: date) -> dict
    # If stored week_start != current week_start, returns a fresh empty record

def save_weekly_record(path: Path, week_start: date, records: dict) -> None
    # Writes {"week_start": ..., "records": records}

def get_missed_tasks(
    schedule: dict[str, list[str]],
    records: dict,
    past_days: list[str]
) -> dict[str, list[str]]
    # Returns {day: [missed_task, ...]} for each past day in the current week
    # A task is "missed" if it appears in the schedule but was not marked True in records
```

### `src/core/checklist.py`
Go-out scenario management. No Streamlit imports.

```python
DEFAULT_SCENARIOS: dict[str, list[str]]

def load_scenarios(path: Path) -> dict[str, list[str]]
def save_scenarios(path: Path, scenarios: dict[str, list[str]]) -> None
def add_scenario(scenarios: dict, name: str) -> dict[str, list[str]]
def remove_scenario(scenarios: dict, name: str) -> dict[str, list[str]]
def add_item(scenarios: dict, scenario: str, item: str) -> dict[str, list[str]]
def remove_item(scenarios: dict, scenario: str, index: int) -> dict[str, list[str]]
```

### `src/core/food.py`
Food inventory management, expiry checks, and category sorting. No Streamlit imports.

```python
VALID_LEVELS: tuple[str, ...] = ("High", "Medium", "Low")
VALID_CATEGORIES: tuple[str, ...] = ("Fresh Produce", "Longer Shelf Life")
EXPIRY_WARNING_DAYS: int = 7

LEVEL_STYLE: dict[str, dict[str, str]] = {
    "High":   {"emoji": "🟢", "bg": "#d4edda", "fg": "#155724"},
    "Medium": {"emoji": "🟡", "bg": "#fff3cd", "fg": "#856404"},
    "Low":    {"emoji": "🔴", "bg": "#f8d7da", "fg": "#721c24"},
}

def load_food(path: Path) -> list[dict]
def save_food(path: Path, items: list[dict]) -> None
def add_item(items: list, name: str, category: str, level: str, expiry_date: date) -> list[dict]
def remove_item(items: list, index: int) -> list[dict]
def update_item(items: list, index: int, level: str) -> list[dict]
    # Updates the level of an existing item

def sort_items(items: list[dict]) -> list[dict]
    # Fresh Produce first, then Longer Shelf Life
    # Within each group: sorted by expiry_date ascending

def is_expiring_soon(expiry_date_str: str, today: date) -> bool
    # Returns True if days_until(expiry_date) <= EXPIRY_WARNING_DAYS
```

### `app.py`
UI only — imports from `src/`, calls functions, renders results. Contains no data transformation logic.

```
Responsibilities:
- Page config, timezone setup via time_utils
- st.tabs() layout with 3 tabs
- Tab 1: render checklist form, on submit call save_weekly_record; show missed tasks panel with catch-up checkboxes (checked tasks are saved as done and disappear on rerun); show schedule editor
- Tab 2: render scenario selector + checklist; show edit expander
- Tab 3: render food list (sorted, color-coded, expiry-flagged); render add-item form
```

---

## 6. Environment & Configuration

### `.env`
```
DATA_DIR=data
TZ=America/Los_Angeles
```
- `pathlib.Path` used for all file paths, derived from `DATA_DIR`
- Loaded via `python-dotenv` at app startup in `app.py`

### `requirements.txt` (pinned)
```
streamlit==1.43.0
pytz==2024.2
python-dotenv==1.0.1
```

---

## 7. Implementation Phases

### Phase 1 — Scaffold & Utilities ✅ Done
**Goal:** Set up correct directory structure; build shared infrastructure.
- [x] Create `src/` with subdirectories and `__init__.py` files
- [x] Write `src/utils/time_utils.py`
- [x] Write `src/database/storage.py` with `StorageError`, `load_json`, `save_json`
- [x] Create `data/` directory; add to `.gitignore`
- [x] Create `.env` and load it in `app.py`

### Phase 2 — Tab 1: Cleaning Tracker ✅ Done
**Goal:** Migrate and extend the existing cleaning tab with weekly record and missed-task reminder.
- [x] Write `src/core/cleaning.py` (schedule CRUD + weekly record + missed task logic)
- [x] Seed `data/cleaning_schedule.json` on first run
- [x] Build Tab 1 UI: checklist form → save to `weekly_record.json` on submit
- [x] Build "Missed This Week" panel: checkboxes for past days' unchecked tasks; checking and submitting marks them done and removes them from the list
- [x] Build schedule editor expander (add/delete tasks, add day)

### Phase 3 — Tab 2: Go-Out Checklist ✅ Done
**Goal:** Build scenario-based checklist feature.
- [x] Write `src/core/checklist.py`
- [x] Seed `data/scenarios.json` on first run
- [x] Build Tab 2 UI: scenario selector, stateless checklist, edit expander

### Phase 4 — Tab 3: Food Inventory ✅ Done
**Goal:** Build the food inventory tracker with category grouping and expiry alerts.
- [x] Write `src/core/food.py` (CRUD + sort + expiry check)
- [x] Initialize `data/food_inventory.json` as `[]` on first run
- [x] Build Tab 3 UI:
  - Add-item form: name, category dropdown, level dropdown, expiry date picker
  - Display two groups: Fresh Produce / Longer Shelf Life
  - Within each group: rows sorted by expiry date, color-coded volume level
  - Items with ≤7 days to expiry: highlighted red regardless of level color
  - Inline level selector + delete button per item

### Phase 5 — Polish & Mobile QA
**Goal:** Ensure usability on phone browser and harden error handling.
- [ ] Review all forms for mobile tap-friendliness
- [ ] Confirm all file I/O wrapped in `try-except` → `st.error` feedback
- [ ] End-to-end test on mobile browser (same WiFi, `http://<local-ip>:8501`)
- [ ] Finalize `requirements.txt`

---

## 8. Error Handling Contract

| Layer | Responsibility |
|---|---|
| `storage.py` | Raises `StorageError` on any I/O or parse failure |
| `src/core/*.py` | Propagates `StorageError`; raises `ValueError` for invalid inputs (bad level, bad date) |
| `app.py` | Catches all errors, calls `st.error()` with a user-readable message; never crashes silently |

---

## 9. Weekly Record Reset Logic

On every app load, `cleaning.py` compares the stored `week_start` against the current Monday:
- If they match → load existing records normally
- If they differ (it's a new week) → discard old records, return empty `records = {}`

This means data is automatically cleared without any cron job or scheduler.

---

## 10. Git Commit Convention

Follow conventional commits (per `CLAUDE.md`):
```
feat: add weekly missed-task reminder panel to cleaning tab
feat: add food inventory with expiry warnings and category grouping
refactor: extract cleaning logic into src/core/cleaning.py
chore: scaffold modular directory structure and storage layer
```

---

## 11. Open Questions / Future Enhancements

| Item | Notes |
|---|---|
| Cloud hosting | Could deploy to Streamlit Community Cloud for remote phone access without WiFi restriction |
| Shopping list | Food inventory could auto-generate a shopping list from Low-level or expiring items |
| More tabs | User may request additional tabs (meal planning, budget, etc.) |
| Cleaning history | Could optionally archive weekly records before reset for long-term analytics |
