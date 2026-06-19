# 🚂 RailChart — IRCTC Chart Window Predictor

> Know **exactly** when to rush to the station counter for a **Current Booking** ticket.

RailChart tells you when Indian Railways will prepare the **first reservation chart** for your train, so you know the precise window when vacant berths become available for current booking at station counters.

---

## 📸 What It Does

- Enter a **train number** → autocomplete shows train name + departure time
- Enter your **journey date**
- Get the **estimated chart preparation window** (e.g., *7:50 PM – 8:15 PM prev. night*)
- Watch a **live countdown** ticking down to that moment
- See the **confidence level** and which IRCTC rule was applied

---

## 🗂️ Project Structure

```
CurrentOpen/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   └── chart.py             # API endpoints
│   ├── services/
│   │   ├── heuristic.py         # Chart time estimation logic
│   │   └── train_lookup.py      # Static train dataset lookup
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── data/
│   │   └── trains.json          # ~200 major Indian trains dataset
│   └── requirements.txt
└── frontend/
    ├── index.html               # Single-page app
    ├── style.css                # Dark glassmorphism design system
    └── app.js                   # UI logic, fetch, countdown, autocomplete
```

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- A modern browser (Chrome, Firefox, Edge)

---

### Step 1 — Install Backend Dependencies

Open a terminal in the project root (`CurrentOpen/`):

```bash
pip install fastapi uvicorn[standard] pydantic python-dateutil
```

---

### Step 2 — Start the Backend Server

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> 💡 The `--reload` flag auto-restarts the server when you edit Python files. Remove it in production.

---

### Step 3 — Open the Frontend

Simply open the HTML file in your browser:

**Option A — Double-click:**
```
frontend/index.html
```

**Option B — From terminal:**
```bash
# Windows
start frontend\index.html

# Or drag index.html into any browser window
```

---

### Step 4 — Use It!

1. Type a train number in the search box (e.g., `12617`, `12951`, `22691`)
2. Select from the autocomplete dropdown
3. Pick your journey date
4. Click **Predict Chart Window**
5. See the chart time + live countdown ⏳

---

## 🔌 API Endpoints

The backend runs at `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |
| `POST` | `/api/chart-estimate` | Get chart window for a train |
| `GET` | `/api/trains/search?q=126` | Search trains by number/name |
| `GET` | `/api/trains/{train_number}` | Get info for a specific train |

### Example API Call

```bash
curl -X POST http://localhost:8000/api/chart-estimate \
  -H "Content-Type: application/json" \
  -d '{"train_number": "12617", "journey_date": "2026-07-20"}'
```

**Response:**
```json
{
  "train_number": "12617",
  "train_name": "MANGALA LAKSHADWEEP",
  "journey_date": "2026-07-20",
  "origin_station": "Hazrat Nizamuddin (NZM)",
  "origin_departure_time": "14:45",
  "first_chart_window": {
    "earliest": "2026-07-19T14:20:00+05:30",
    "latest":   "2026-07-19T15:10:00+05:30"
  },
  "current_booking_opens": "2026-07-19T14:20:00+05:30",
  "confidence": 0.75,
  "method": "heuristic",
  "rule_applied": "Departure 14:01–23:59 → Chart ~10 hours before departure",
  "notes": "...",
  "disclaimer": "..."
}
```

---

## 📐 How the Charting Rules Work

Official IRCTC Railway Board rules (as of 2025-26):

| Train Departure | First Chart Prepared At |
|---|---|
| **5:00 AM – 2:00 PM** | **8:00 PM the previous night** |
| **2:01 PM – 11:59 PM** | **~10 hours before departure** |
| **12:00 AM – 4:59 AM** | **~10 hours before** (often previous afternoon) |

After the first chart → **Current Booking opens immediately** at station counters.  
A **final chart** is released ~30 min before departure for any last-minute changes.

---

## 🛠️ Development Notes

### Adding More Trains

Edit `backend/data/trains.json` and add entries in this format:

```json
{
  "train_number": "12345",
  "train_name": "MY EXPRESS",
  "origin_station_code": "NDLS",
  "origin_station_name": "New Delhi",
  "departure_time": "18:30"
}
```

### Changing the API Port

1. Edit `backend/main.py` (or pass `--port XXXX` to uvicorn)
2. Update `API_BASE` in `frontend/app.js` line 10:
   ```js
   const API_BASE = 'http://localhost:YOUR_PORT';
   ```

---

## ⚠️ Disclaimer

RailChart is an **independent, unofficial tool** and is **not affiliated with IRCTC or Indian Railways**.

All chart time estimates are based on publicly available Railway Board directives (2025-26). Actual charting may vary by ±15–60 minutes. Always verify at the station counter or IRCTC app before making decisions.

---

## 🗺️ Roadmap

- [x] **MVP** — Heuristic engine + FastAPI + HTML/CSS/JS UI
- [x] Static train dataset (~200 major trains)
- [x] Autocomplete search
- [x] Live countdown timer
- [ ] **V2** — Expanded train database (all trains from open datasets)
- [ ] **V3** — Historical chart-time data collection (detect actual chart times)
- [ ] **V4** — Confidence scores from real data, per-train accuracy
- [ ] **V5** — Push notifications when chart window opens

---

*Built with ❤️ for Indian rail passengers · Data: IRCTC Railway Board Directives 2025-26*
