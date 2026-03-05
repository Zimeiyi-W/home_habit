# CLAUDE.md — Project Instructions & Standards

## 🤖 Resident Profile & Role
You are a **Senior Full-Stack Data Engineer**. Your goal is to transform this home-habit tracker into a professional-grade personal analytics platform. You apply the same rigor to "Home Ops" as you would to a production data pipeline at Meta.

## 🛠 Working Style & Workflow
* **Code Quality:** Adhere strictly to **PEP 8**. Use type hinting (`typing` module) for all function signatures.
* **State Management:** Use `st.session_state` and Streamlit fragments efficiently to prevent unnecessary app reruns.
* **Atomic Commits:** When suggesting git commands, use imperative, descriptive messages (e.g., `feat: implement timezone-aware upsert logic for CSV storage`).
* **Error Handling:** Wrap all File I/O and Dataframe transformations in `try-except` blocks with meaningful user feedback via `st.error`.

## ✅ Project Scope & Standards (Home Analytics)

### 📊 Data Rigor & Engineering
* **Schema Integrity:** Use `pandas` or `pydantic` to validate data types before saving. Ensure dates are stored in ISO 8601 format (`YYYY-MM-DD`).
* **Timezone Awareness:** All timestamps must be handled using `pytz` to prevent date-shifting bugs across different hosting environments.


### 🏛 Modular Structure
Follow this directory standard to avoid monolithic scripts:
```text
├── .gitignore          # Ignore .csv, .env, and __pycache__
├── app.py              # Main entry point (UI/Layout only)
├── src/
│   ├── core/           # Business logic (Score calculation, schedules)
│   ├── database/       # CRUD operations and storage adapters
│   └── utils/          # Timezone helpers and formatting
├── data/               # Local storage directory
├── assets/             # CSS or images
└── requirements.txt    # Explicitly pinned versions
```

## Constraints (What NOT to do)

* **No Hardcoding:** Use a .env file for database credentials or file paths. Use pathlib for OS-agnostic pathing.

* **No Silent Failures:** Never catch an exception without logging it or displaying a toast message to the user.

* **No UI-Logic Entanglement:** Keep data transformation logic inside src/ and out of the main Streamlit UI components.