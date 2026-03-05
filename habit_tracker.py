import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz  # Handles timezone conversions
import os

# 1. Setup & Data Loading
st.set_page_config(page_title="Meiyi's Home Reset", layout="centered")
# Set the local timezone
local_tz = pytz.timezone("America/Los_Angeles") 
# This gets the current time in my timezone
now_local = datetime.now(local_tz)
today = now_local.date()

DB_FILE = "habit_history.csv"

# Helper to load data reliably
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Ensure Date is always a date object for comparison
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=["Date", "Score"])

# Initialize data in session state so it doesn't reload constantly
if 'history' not in st.session_state:
    st.session_state.history = load_data()

# 2. Daily Schedule Logic
cleaning_schedule = {
    "Monday": ["Vacuum Floors", "Wipe Kitchen Counters", "Empty Trash - Monday night", "Fridge Clear-out"],
    "Tuesday": ["Scrub Toilets", "Clean Mirrors", "Sink Scrub"],
    "Wednesday": ["Dust Electronics", "Dust Shelves"],
    "Thursday": ["Vacuum Floors", "Organize Clothes"],
    "Friday": ["Organize Pantry"],
    "Saturday": ["Clean Stove", "Clean Yards"],
    "Sunday": ["Vacuum Floors", "Laundry - Wash & Fold"]
}

# 3. UI Header
st.title("🏠 Home Habit Tracker")

day_name = today.strftime("%A")
st.subheader(f"Today is {day_name}, {today}")

# 4. Interactive Checklist
tasks = cleaning_schedule.get(day_name, [])
completed_count = 0

st.write("### Today's Tasks")
# Using a form helps prevent the app from rerunning every single time I check a box
with st.form("daily_form"):
    for task in tasks:
        if st.checkbox(task, key=f"chk_{task}"):
            completed_count += 1
    
    submit_button = st.form_submit_button("Save Daily Progress")

# 5. The "Habit Score" Calculation
total_tasks = len(tasks)
score = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

# 6. Saving Logic (Triggered only by the Form Button)
if submit_button:
    df_history = st.session_state.history
    
    if not df_history.empty and today in df_history['Date'].values:
        df_history.loc[df_history['Date'] == today, 'Score'] = score
        st.toast(f"Updated record for {today}!")
    else:
        new_entry = pd.DataFrame([{"Date": today, "Score": score}])
        df_history = pd.concat([df_history, new_entry], ignore_index=True)
        st.toast(f"New record saved for {today}!")
    
    # Update session state and file
    st.session_state.history = df_history
    df_history.to_csv(DB_FILE, index=False)

# 7. Visualization
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

# Show a small trend chart using the session state data
if not st.session_state.history.empty:
    st.write("### Weekly Momentum")
    # Sort by date so the chart makes sense
    chart_data = st.session_state.history.sort_values("Date")
    st.line_chart(chart_data.set_index("Date")["Score"])