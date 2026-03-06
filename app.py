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
from src.core.checklist import (
    add_item as checklist_add_item,
    add_scenario,
    load_scenarios,
    remove_item as checklist_remove_item,
    remove_scenario,
    save_scenarios,
)
from src.database.storage import StorageError
from src.utils.time_utils import get_day_name, get_today, get_week_start

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))
TZ: str = os.getenv("TZ", "America/Los_Angeles")

SCHEDULE_PATH: Path = DATA_DIR / "cleaning_schedule.json"
WEEKLY_RECORD_PATH: Path = DATA_DIR / "weekly_record.json"
SCENARIOS_PATH: Path = DATA_DIR / "scenarios.json"

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
        with st.form("missed_tasks_form"):
            catch_up: dict[str, dict[str, bool]] = {}
            for day, tasks in missed.items():
                with st.expander(f"{day} — {len(tasks)} missed", expanded=True):
                    catch_up[day] = {}
                    for t in tasks:
                        catch_up[day][t] = st.checkbox(
                            t, value=False, key=f"missed_{day}_{t}"
                        )

            submitted_missed = st.form_submit_button(
                "✅ Mark as Completed", use_container_width=True
            )

        if submitted_missed:
            try:
                for day, task_checks in catch_up.items():
                    day_record = records.get(day, {})
                    for task, done in task_checks.items():
                        if done:
                            day_record[task] = True
                    records[day] = day_record
                save_weekly_record(WEEKLY_RECORD_PATH, week_start, records)
                st.success("Catch-up tasks saved!")
                st.rerun()
            except StorageError as exc:
                st.error(f"Could not save catch-up tasks: {exc}")

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
    # ── Load scenarios ────────────────────────────────────────────────────────
    try:
        scenarios: dict[str, list[str]] = load_scenarios(SCENARIOS_PATH)
    except StorageError as exc:
        st.error(f"Could not load scenarios: {exc}")
        st.stop()

    scenario_names: list[str] = list(scenarios.keys())

    if not scenario_names:
        st.info("No scenarios yet. Add one below.")
    else:
        # ── Scenario selector ─────────────────────────────────────────────────
        selected: str = st.selectbox(
            "Select a scenario", scenario_names, key="scenario_selector"
        )

        st.subheader(f"🎒 {selected}")

        items: list[str] = scenarios.get(selected, [])
        if not items:
            st.caption("No items in this scenario yet.")
        else:
            # Stateless checklist — state is not persisted
            for item in items:
                st.checkbox(item, value=False, key=f"goout_{selected}_{item}")

    st.divider()

    # ── Edit scenarios expander ───────────────────────────────────────────────
    with st.expander("✏️ Edit Scenarios", expanded=False):
        # Reload to reflect any changes made above in the same session
        try:
            scenarios = load_scenarios(SCENARIOS_PATH)
        except StorageError as exc:
            st.error(f"Could not load scenarios for editing: {exc}")
            st.stop()

        scenario_names = list(scenarios.keys())

        for scenario_name in scenario_names:
            st.markdown(f"**{scenario_name}**")
            scenario_items = scenarios[scenario_name]

            if scenario_items:
                for idx, it in enumerate(scenario_items):
                    col_item, col_btn = st.columns([5, 1])
                    col_item.markdown(it)
                    if col_btn.button("🗑", key=f"del_item_{scenario_name}_{idx}", help=f"Remove '{it}'"):
                        try:
                            updated = checklist_remove_item(scenarios, scenario_name, idx)
                            save_scenarios(SCENARIOS_PATH, updated)
                            st.success(f"Removed '{it}' from '{scenario_name}'.")
                            st.rerun()
                        except (StorageError, ValueError) as exc:
                            st.error(f"Could not remove item: {exc}")
            else:
                st.caption("No items yet.")

            # Add item inline
            with st.form(f"add_item_{scenario_name}"):
                new_item = st.text_input(
                    "New item",
                    placeholder="e.g. Sunscreen",
                    key=f"new_item_{scenario_name}",
                )
                col_add, col_del = st.columns([3, 1])
                add_clicked = col_add.form_submit_button(f"+ Add item")
                del_clicked = col_del.form_submit_button("🗑 Delete scenario")

            if add_clicked:
                try:
                    updated = checklist_add_item(scenarios, scenario_name, new_item)
                    save_scenarios(SCENARIOS_PATH, updated)
                    st.success(f"Added '{new_item.strip()}' to '{scenario_name}'.")
                    st.rerun()
                except (StorageError, ValueError) as exc:
                    st.error(f"Could not add item: {exc}")

            if del_clicked:
                try:
                    updated = remove_scenario(scenarios, scenario_name)
                    save_scenarios(SCENARIOS_PATH, updated)
                    st.success(f"Deleted scenario '{scenario_name}'.")
                    st.rerun()
                except (StorageError, ValueError) as exc:
                    st.error(f"Could not delete scenario: {exc}")

            st.markdown("---")

        # Add a new scenario
        st.markdown("**Add a new scenario**")
        with st.form("add_scenario_form"):
            new_scenario = st.text_input("Scenario name", placeholder="e.g. Beach day")
            if st.form_submit_button("+ Add Scenario"):
                try:
                    updated = add_scenario(scenarios, new_scenario)
                    save_scenarios(SCENARIOS_PATH, updated)
                    st.success(f"Added scenario '{new_scenario.strip()}'.")
                    st.rerun()
                except (StorageError, ValueError) as exc:
                    st.error(f"Could not add scenario: {exc}")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Food Inventory
# ══════════════════════════════════════════════════════════════════════════════
with tab_food:
    st.info("Food Inventory — coming in Phase 4.")
