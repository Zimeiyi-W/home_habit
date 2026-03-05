"""app.py — Entry point for the Home Analytics Platform.

Responsibilities:
- Load environment config via python-dotenv
- Configure the Streamlit page
- Wire up tab routing (UI only; all logic lives in src/)
"""

import os
from datetime import date
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.core.cleaning import (
    ORDERED_DAYS,
    add_day,
    add_task,
    get_missed_tasks,
    load_schedule,
    load_weekly_record,
    remove_task,
    save_schedule,
    save_weekly_record,
)
from src.database.storage import StorageError
from src.utils.time_utils import get_day_name, get_today, get_week_start

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))
TZ: str = os.getenv("TZ", "America/Los_Angeles")

SCHEDULE_PATH: Path = DATA_DIR / "cleaning_schedule.json"
WEEKLY_RECORD_PATH: Path = DATA_DIR / "weekly_record.json"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏠 Home Analytics",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Shared time context (computed once per run) ───────────────────────────────
today: date = get_today(TZ)
day_name: str = get_day_name(TZ)
week_start: date = get_week_start(TZ)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏠 Home Analytics")
st.caption(f"{day_name}, {today}  •  Week of {week_start}")

# ── Tab layout ────────────────────────────────────────────────────────────────
tab_cleaning, tab_goout, tab_food = st.tabs(
    ["🧹 Cleaning", "🎒 Go-Out Checklist", "🥦 Food Inventory"]
)

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Cleaning Tracker
# ══════════════════════════════════════════════════════════════════════════════
with tab_cleaning:
    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        schedule: dict[str, list[str]] = load_schedule(SCHEDULE_PATH)
        records: dict[str, dict[str, bool]] = load_weekly_record(
            WEEKLY_RECORD_PATH, week_start
        )
    except StorageError as exc:
        st.error(f"Could not load cleaning data: {exc}")
        st.stop()

    # ── Today's task checklist ─────────────────────────────────────────────────
    today_tasks: list[str] = schedule.get(day_name, [])

    st.subheader(f"Today — {day_name}")

    if not today_tasks:
        st.info("No tasks scheduled for today. Enjoy your day! 🎉")
    else:
        # Pre-fill checkboxes from any previously saved state for today
        saved_today: dict[str, bool] = records.get(day_name, {})

        with st.form("cleaning_form"):
            checked: dict[str, bool] = {}
            for task in today_tasks:
                checked[task] = st.checkbox(
                    task, value=saved_today.get(task, False), key=f"task_{task}"
                )

            submitted = st.form_submit_button("✅ Save Today's Tasks", use_container_width=True)

        if submitted:
            try:
                records[day_name] = checked
                save_weekly_record(WEEKLY_RECORD_PATH, week_start, records)
                st.success("Tasks saved!")
            except StorageError as exc:
                st.error(f"Could not save tasks: {exc}")

    st.divider()

    # ── Missed This Week panel ─────────────────────────────────────────────────
    # Compute past days (days before today in the current week's order)
    week_days_so_far = [
        d for d in ORDERED_DAYS
        if d != day_name and ORDERED_DAYS.index(d) < ORDERED_DAYS.index(day_name)
    ]

    missed: dict[str, list[str]] = get_missed_tasks(schedule, records, week_days_so_far)

    st.subheader("⚠️ Missed This Week")
    if not missed:
        st.success("Nothing missed so far this week!")
    else:
        for day, tasks in missed.items():
            with st.expander(f"{day} — {len(tasks)} missed", expanded=True):
                for t in tasks:
                    st.markdown(f"- {t}")

    st.divider()

    # ── Schedule Editor ────────────────────────────────────────────────────────
    with st.expander("📋 Edit Weekly Schedule", expanded=False):
        # Reload schedule (may have been mutated above in the same session)
        try:
            schedule = load_schedule(SCHEDULE_PATH)
        except StorageError as exc:
            st.error(f"Could not load schedule for editing: {exc}")
            st.stop()

        for day in ORDERED_DAYS:
            if day not in schedule:
                continue
            st.markdown(f"**{day}**")
            tasks_for_day = schedule[day]
            if tasks_for_day:
                for idx, task in enumerate(tasks_for_day):
                    col_task, col_btn = st.columns([5, 1])
                    col_task.markdown(task)
                    if col_btn.button("🗑", key=f"del_{day}_{idx}", help=f"Remove '{task}'"):
                        try:
                            updated = remove_task(schedule, day, idx)
                            save_schedule(SCHEDULE_PATH, updated)
                            st.success(f"Removed '{task}' from {day}.")
                            st.rerun()
                        except (StorageError, ValueError) as exc:
                            st.error(f"Could not remove task: {exc}")
            else:
                st.caption("No tasks yet.")

            # Add task inline
            with st.form(f"add_task_{day}"):
                new_task = st.text_input(
                    "New task", placeholder="e.g. Clean Bathroom", key=f"new_task_{day}"
                )
                if st.form_submit_button(f"+ Add to {day}"):
                    try:
                        updated = add_task(schedule, day, new_task)
                        save_schedule(SCHEDULE_PATH, updated)
                        st.success(f"Added '{new_task.strip()}' to {day}.")
                        st.rerun()
                    except (StorageError, ValueError) as exc:
                        st.error(f"Could not add task: {exc}")

            st.markdown("---")

        # Add a new day
        st.markdown("**Add a new day**")
        with st.form("add_day_form"):
            new_day = st.text_input("Day name", placeholder="e.g. Holiday")
            if st.form_submit_button("+ Add Day"):
                try:
                    updated = add_day(schedule, new_day)
                    save_schedule(SCHEDULE_PATH, updated)
                    st.success(f"Added day '{new_day.strip()}'.")
                    st.rerun()
                except (StorageError, ValueError) as exc:
                    st.error(f"Could not add day: {exc}")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Go-Out Checklist
# ══════════════════════════════════════════════════════════════════════════════
with tab_goout:
    st.info("Go-Out Checklist — coming in Phase 3.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Food Inventory
# ══════════════════════════════════════════════════════════════════════════════
with tab_food:
    st.info("Food Inventory — coming in Phase 4.")
