# Concurrency & Locking in RailChart

This document explains the race condition challenge in RailChart's file-based database and how the backend uses asynchronous locking to guarantee data integrity.

---

## ⚠️ The Concurrency Challenge

FastAPI runs on an asynchronous event loop, allowing it to handle many incoming client requests concurrently. 

When a user estimates the charting window of a train that is **not found** in our database, the backend:
1. Initiates an asynchronous web lookup via Gemini Search (`fetch_and_cache_train_from_gemini`).
2. Reads the existing contents of `backend/data/trains.json`.
3. Appends the newly discovered train record.
4. Writes the updated list back to `trains.json`.
5. Updates the in-memory cache `_train_db`.

### The Race Condition
If two users simultaneously search for two different missing trains (e.g. User A searches for `12007` and User B searches for `12027` at the same second):
1. **Request A** reads `trains.json`.
2. **Request B** reads `trains.json` before Request A has finished writing.
3. **Request A** appends `12007` and writes the file.
4. **Request B** appends `12027` to its *outdated* copy and writes the file, **overwriting and erasing** the changes made by Request A.
5. In worse cases, concurrent writes can overlap, resulting in truncated files or invalid JSON parsing errors.

---

## 🔒 The Solution: Async File Locking

To prevent race conditions, the backend implements a thread-safe serialization lock using **`asyncio.Lock()`** in [train_lookup.py](file:///C:/Users/navad/CurrentOpen/backend/services/train_lookup.py).

### How it works:
```python
import asyncio

_write_lock = asyncio.Lock()

async def fetch_and_cache_train_from_gemini(train_number: str):
    # 1. Fetch data from Gemini (outside the lock to avoid blocking other lookups)
    data = await fetch_data_from_api(...)

    # 2. Acquire lock to perform read-modify-write operations safely
    async with _write_lock:
        # Re-read trains.json inside the lock to ensure we have the latest state
        with open("trains.json", "r") as f:
            trains = json.load(f)

        # Check if the train was already cached by another concurrent request
        if not exists(data, trains):
            trains.append(data)
            trains.sort(key=lambda x: x["train_number"])

            # Save changes back to disk
            with open("trains.json", "w") as f:
                json.dump(trains, f, indent=2)
```

### Key Guardrails:
- **Lock Scope:** The lock is only held during the file I/O operations (`read` -> `modify` -> `write` -> `update cache`). The network request to the Gemini API is made *before* acquiring the lock, ensuring the server can fetch multiple timetables concurrently without blocking.
- **Double-Check Pattern:** Once the lock is acquired, the file is re-read and checked. If another request already resolved the train while this request was waiting for the lock, it skips appending the duplicate entry.
