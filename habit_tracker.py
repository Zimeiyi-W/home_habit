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
    "Monday": ["Vacuum Floors", "Wipe Kitchen Counters", "Empty Trash - Monday night", "Fridge Clear-out"],
    "Tuesday": ["Scrub Toilets", "Clean Mirrors", "Sink Scrub"],
    "Wednesday": ["Dust Electronics", "Dust Shelves"],
    "Thursday": ["Vacuum Floors", "Organize Clothes"],
    "Friday": ["Organize Pantry"],
    "Saturday": ["Clean Stove", "Clean Yards"],
    "Sunday": ["Vacuum Floors", "Laundry - Wash & Fold"]
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

# 7. Historical Tracking (Optimized for Daily Uniqueness)
if st.button("Save Daily Progress"):
    df_history = load_data()
    
    # Ensure the Date column is in datetime format for reliable comparison
    df_history['Date'] = pd.to_datetime(df_history['Date']).dt.date
    
    # Create the new entry record
    new_entry = {"Date": today, "Score": score}
    
    if not df_history.empty and today in df_history['Date'].values:
        # Update the existing row for today
        df_history.loc[df_history['Date'] == today, 'Score'] = score
        st.toast(f"Updated record for {today}!")
    else:
        # Append as a new row if today doesn't exist yet
        df_history = pd.concat([df_history, pd.DataFrame([new_entry])], ignore_index=True)
        st.toast(f"New record saved for {today}!")
    
    # Save back to CSV
    df_history.to_csv(DB_FILE, index=False)
    st.toast("Progress Saved!")

# Show a small trend chart if data exists
df_history = load_data()
if not df_history.empty:
    st.write("### Weekly Momentum")
    st.line_chart(df_history.set_index("Date")["Score"])