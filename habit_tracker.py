import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Setup & Data Loading
st.set_page_config(page_title="Meiyi's Home Reset", layout="centered")
DB_FILE = "habit_history.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Date", "Task", "Completed"])

# 2. Daily Schedule Logic
cleaning_schedule = {
    "Monday": ["Wipe Counters", "Empty Trash", "Fridge Clear-out"],
    "Tuesday": ["Scrub Toilets", "Clean Mirrors", "Sink Scrub"],
    "Wednesday": ["Dust Electronics", "Dust Shelves"],
    "Thursday": ["Vacuum Floors", "Mop Kitchen"],
    "Friday": ["Bed Sheets", "Towels", "Fold Laundry"],
    "Saturday": ["Deep Project (Pantry/Oven)"],
    "Sunday": ["Meal Prep", "Week Planning"]
}

# 3. UI - Sidebar & Header
st.title("🏠 Home Habit Tracker")
today = date.today()
day_name = today.strftime("%A")
st.subheader(f"Today is {day_name}, {today}")

# 4. Interactive Checklist
tasks = cleaning_schedule.get(day_name, [])
completed_count = 0

st.write("### Today's Tasks")
for task in tasks:
    if st.checkbox(task, key=task):
        completed_count += 1

# 5. The "Habit Score" Calculation
total_tasks = len(tasks)
score = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

# 6. Visualization
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Today's Score", value=f"{score:.0f}%", delta=f"{score - 50:.0f}% vs Target")

with col2:
    if score == 100:
        st.success("Perfect Day! 🏆")
    elif score >= 50:
        st.info("Good progress!")
    else:
        st.warning("Keep going!")

# 7. Historical Tracking (Simplified)
if st.button("Save Daily Progress"):
    df = load_data()
    new_entry = pd.DataFrame([{"Date": today, "Score": score}])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    st.toast("Progress Saved!")

# Show a small trend chart if data exists
df_history = load_data()
if not df_history.empty:
    st.write("### Weekly Momentum")
    st.line_chart(df_history.set_index("Date")["Score"])