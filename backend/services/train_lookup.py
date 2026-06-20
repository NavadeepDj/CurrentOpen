"""
RailChart — Train Timetable Lookup Service

Uses a bundled static JSON dataset of Indian Express/Mail trains.
Data sourced from open datasets (datameet/railways) and publicly
available NTES timetable information.

Each train entry contains:
  - train_number
  - train_name
  - origin_station_code
  - origin_station_name
  - departure_time  (HH:MM at origin station)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from backend.models.schemas import TrainInfo, TrainSearchResult

import os
import asyncio
from google import genai
from google.genai import types

_DATA_FILE = Path(__file__).parent.parent / "data" / "trains.json"

_train_db: dict[str, dict] = {}
_loaded = False
_write_lock = asyncio.Lock()


def _load_db() -> None:
    global _train_db, _loaded
    if _loaded:
        return
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        trains: list[dict] = json.load(f)
    for t in trains:
        _train_db[t["train_number"].strip()] = t
    _loaded = True


async def get_train_info(train_number: str) -> Optional[TrainInfo]:
    """
    Lookup train info by train number.
    Returns None if not found in the static dataset.
    """
    _load_db()
    num = train_number.strip().upper()
    record = _train_db.get(num)
    if record is None:
        return None
    return TrainInfo(
        train_number=record["train_number"],
        train_name=record["train_name"],
        origin_station_code=record["origin_station_code"],
        origin_station_name=record["origin_station_name"],
        origin_departure_time=record["departure_time"],
    )


async def search_trains(query: str, limit: int = 10) -> list[TrainSearchResult]:
    """
    Search trains by number or name prefix.
    """
    _load_db()
    q = query.strip().lower()
    results: list[TrainSearchResult] = []
    for num, rec in _train_db.items():
        if num.startswith(q.upper()) or q in rec["train_name"].lower():
            results.append(
                TrainSearchResult(
                    train_number=rec["train_number"],
                    train_name=rec["train_name"],
                    origin_station_code=rec["origin_station_code"],
                    origin_station_name=rec["origin_station_name"],
                    departure_time=rec["departure_time"],
                )
            )
            if len(results) >= limit:
                break
    return results


async def fetch_and_cache_train_from_gemini(train_number: str) -> Optional[TrainInfo]:
    """
    Query Gemini 2.5 Flash with search grounding to fetch the missing train timetable,
    append it to trains.json (thread-safe), and update in-memory cache.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    train_number_clean = train_number.strip()
    prompt = (
        f"Search the web for the official timetable details of Indian Railways train number '{train_number_clean}'. "
        "Find its name, origin station code, origin station name, and its scheduled departure time from the origin station. "
        "Provide the output strictly as a single JSON object in the following format (no markdown code blocks, just raw JSON text): "
        "{\n"
        '  "train_number": "...",\n'
        '  "train_name": "...",\n'
        '  "origin_station_code": "...",\n'
        '  "origin_station_name": "...",\n'
        '  "departure_time": "HH:MM"\n'
        "}\n"
        "Ensure: \n"
        "- departure_time is in 24-hour HH:MM format.\n"
        "- train_name is in UPPERCASE.\n"
        "- origin_station_code is in UPPERCASE (e.g. MAS, NDLS).\n"
        "- origin_station_name is the proper name of the station.\n"
    )

    try:
        def run_api():
            client = genai.Client(api_key=api_key)
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    temperature=0.1
                )
            )
            return response.text

        response_text = await asyncio.to_thread(run_api)
        if not response_text:
            return None

        # Clean markdown wrapper if LLM included it
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        data = json.loads(cleaned_text)

        # Validate fields
        required = ["train_number", "train_name", "origin_station_code", "origin_station_name", "departure_time"]
        if not all(k in data for k in required):
            return None

        # Normalize fields
        data["train_number"] = str(data["train_number"]).strip()
        data["train_name"] = str(data["train_name"]).strip().upper()
        data["origin_station_code"] = str(data["origin_station_code"]).strip().upper()
        data["origin_station_name"] = str(data["origin_station_name"]).strip()
        data["departure_time"] = str(data["departure_time"]).strip()

        # Update trains.json under lock
        async with _write_lock:
            # Re-read file to verify state
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                trains: list[dict] = json.load(f)

            # Check if it was added by another task while we were fetching
            exists = False
            for i, t in enumerate(trains):
                if t["train_number"].strip() == data["train_number"]:
                    trains[i] = data
                    exists = True
                    break

            if not exists:
                trains.append(data)

            # Keep list sorted by train number
            trains.sort(key=lambda x: x["train_number"])

            # Save back to disk
            with open(_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(trains, f, indent=2)

            # Update cache
            _train_db[data["train_number"]] = data

        return TrainInfo(
            train_number=data["train_number"],
            train_name=data["train_name"],
            origin_station_code=data["origin_station_code"],
            origin_station_name=data["origin_station_name"],
            origin_departure_time=data["departure_time"]
        )

    except Exception as e:
        print(f"Error fetching train {train_number} via Gemini: {e}")
        return None
