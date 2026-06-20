# Data Fetching & LLM Timetable Population

This document explains the dynamic timetable search system, the missing train logging mechanism, and how to use a Gemini 3.5 Flash model to bulk-populate the static dataset.

---

## ⚡ Dynamic Retrieval & Caching Flow

When a user estimates the charting window of a train number, the backend automatically performs a lookup in the static [trains.json](file:///C:/Users/navad/CurrentOpen/backend/data/trains.json) file.

If the train is **not found**:
- If `GEMINI_API_KEY` is present in the environment variables, the backend calls the **Google Gen AI SDK (`google-genai`)** using the `gemini-2.5-flash` model with Google Search grounding enabled.
- The model searches the web for the train schedule, extracts the train details into a clean JSON structure, writes it back to `trains.json` using a thread-safe lock, and returns the prediction instantly.
- If `GEMINI_API_KEY` is missing or the search fails, the backend appends the train number to [missing_trains.log](file:///C:/Users/navad/CurrentOpen/backend/data/missing_trains.log) and returns a friendly `404` error.

---

## 🛠️ Bulk Fetcher Utility

We provide an offline utility [fetch_missing_trains.py](file:///C:/Users/navad/CurrentOpen/fetch_missing_trains.py) in the root folder to resolve and cache all logged missing trains at once.

### Usage:
1. Ensure your virtual environment is active and `GEMINI_API_KEY` is configured:
   ```powershell
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="your_api_key_here"
   ```
2. Run the utility:
   ```bash
   .venv\Scripts\python fetch_missing_trains.py
   ```
3. The script will:
   - Read all train numbers in `missing_trains.log`.
   - Resolve their schedules using Gemini Search grounding.
   - Cache them in `trains.json` (sorted automatically).
   - Remove successfully resolved trains from `missing_trains.log` while keeping any failed ones for a future retry.

---

## 🤖 Direct LLM Prompt for Data Curation

If you want to manually run a Gemini 3.5 Flash model (in a chat or script) to generate data for `trains.json`, use the following prompt:

```text
You are a railway data extraction assistant. Your task is to find the official timetables of missing Indian trains and format them for our JSON database.

For each missing train number:
1. Search the web for "[Train Number] origin station and departure time".
2. Extract:
   - train_number (5 digits)
   - train_name (in UPPERCASE, e.g., "PINAKINI SF EXP")
   - origin_station_code (in UPPERCASE, e.g., "MAS")
   - origin_station_name (Proper Case, e.g., "MGR Chennai Central")
   - departure_time (HH:MM in 24-hour format)
3. Return the exact valid JSON records to append.

Here is the list of missing train numbers:
[INSERT MISSING TRAIN NUMBERS HERE]
```

### Example Target Output:
```json
[
  {
    "train_number": "12712",
    "train_name": "PINAKINI SF EXP",
    "origin_station_code": "MAS",
    "origin_station_name": "MGR Chennai Central",
    "departure_time": "14:05"
  }
]
```
Simply append the output list to the arrays in `backend/data/trains.json` and sort them by `train_number`.
