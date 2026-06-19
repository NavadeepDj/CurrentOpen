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

_DATA_FILE = Path(__file__).parent.parent / "data" / "trains.json"

_train_db: dict[str, dict] = {}
_loaded = False


def _load_db() -> None:
    global _train_db, _loaded
    if _loaded:
        return
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        trains: list[dict] = json.load(f)
    for t in trains:
        _train_db[t["train_number"].strip()] = t
    _loaded = True


def get_train_info(train_number: str) -> Optional[TrainInfo]:
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


def search_trains(query: str, limit: int = 10) -> list[TrainSearchResult]:
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
