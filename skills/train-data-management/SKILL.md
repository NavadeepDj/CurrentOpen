---
name: train-data-management
description: Indian Railways timetable caching, boundary-condition verification, local dev upkeep, and UI aesthetics.
---

# Train Data Management & Verification Skill

This workspace skill provides instructions, tools, and guidelines for AI agents to maintain and verify the RailChart application data, local Windows environment configuration, and front-end interface quality.

---

## 🗂️ Timetable Data & Caching

### trains.json Schema
The static database of train timetables is stored at [trains.json](file:///C:/Users/navad/CurrentOpen/backend/data/trains.json). Each entry must follow this exact schema:
```json
{
  "train_number": "12744",
  "train_name": "VIKRAMASIMHAPURI EXP",
  "origin_station_code": "BZA",
  "origin_station_name": "Vijayawada Jn",
  "departure_time": "18:00"
}
```
- `train_number`: String, 5 digits.
- `train_name`: String, UPPERCASE.
- `origin_station_code`: String, UPPERCASE (e.g. MAS, NDLS, TVC).
- `origin_station_name`: String, Proper Title Case.
- `departure_time`: String, 24-hour format `HH:MM`.

### Automated Timetable Retrieval
If a train is missing from the database:
1. **Dynamic Caching:** When `GEMINI_API_KEY` is configured in the environment, the backend automatically queries `gemini-2.5-flash` with Google Search grounding to find the timetable, write it to `trains.json`, and serve it to the user.
2. **Missing Trains Log:** If the lookup fails or `GEMINI_API_KEY` is missing, the backend logs the missing train to [missing_trains.log](file:///C:/Users/navad/CurrentOpen/backend/data/missing_trains.log).
3. **Bulk Fetch Utility:** Run the batch processor utility to resolve all logged missing trains and append them to the database:
   ```bash
   .venv\Scripts\python fetch_missing_trains.py
   ```

---

## 📐 Charting Rules & Time Boundary Correctness

Official IRCTC rules (2025-26) specify 3 departure time windows for predicting the first charting time:

| Departure Window | First Chart Expected | Rule Code Check |
|---|---|---|
| **05:00 – 14:00** | **20:00 (8:00 PM) previous evening** | `5 * 60 <= dep_mins <= 14 * 60` |
| **14:01 – 23:59** | **~10 hours before departure** | `14 * 60 < dep_mins <= 23 * 60 + 59` |
| **00:00 – 04:59** | **~10 hours before departure** | `else` |

### Critical Rule for Coding Boundary Checks
> [!IMPORTANT]
> Always verify boundary check conditions using **minutes-from-midnight** (e.g., `dep_hour * 60 + dep_minute`). 
> **Never** use simple hour integers (e.g., `dep_hour <= 14`) because this incorrectly routes departure times like `14:05` (hour `14`) into the `05:00–14:00` previous-night rule.

---

## 🛠️ Local Dev Environment & Upkeep (Windows)

### 1. Virtual Environment Activation
Always use the local `.venv` environment to run Python commands:
```powershell
# Activation
.venv\Scripts\activate

# Running the FastAPI backend (within workspace root)
.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

### 2. Timezone Verification
On Windows, Python's native `zoneinfo` module will raise a `ZoneInfoNotFoundError` for `"Asia/Kolkata"` unless the **`tzdata`** package is installed. Always ensure `tzdata` is present in `requirements.txt` and installed in `.venv`.

### 3. Port Conflicts (`WinError 10013`)
If uvicorn fails to start with `WinError 10013`, it means port `8000` is already occupied by a background server process.
- **Resolution:** Identify and stop the background server process using `manage_task` or kill the listening process.
  ```powershell
  # Check if port is bound (PowerShell)
  Get-NetTCPConnection -LocalPort 8000
  ```

---

## 🎨 UI Aesthetic & Design Guidelines

To preserve the RailChart premium design:
- **Theme:** Dark theme is default. Uses deep navy background (`#0D1117`), electric indigo (`#6366F1`) primary highlights, and amber (`#F59E0B`) alerts. 
- **Glassmorphism:** Apply `backdrop-filter: blur(12px)` and thin semi-transparent borders for cards.
- **Countdown Timer:** Live-updating countdown (`app.js` -> `startCountdown`) must use `requestAnimationFrame` or reflow triggers (`el.offsetWidth`) for the flip/tick character animations.
- **Autocomplete:** autocomplete input queries must be debounced by at least `280ms` to prevent spamming the `/api/trains/search` endpoint.
