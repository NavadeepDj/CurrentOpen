"""
RailChart — Heuristic Chart Time Estimator

Official IRCTC rules (as of 2025-26):
  • Trains departing 05:00–14:00 → first chart by 20:00 prev. night
  • Trains departing 14:01–23:59 → first chart ~10 hours before departure
  • Trains departing 00:00–04:59 → first chart ~10 hours before departure
                                  (often falls on previous afternoon/evening)

After the first chart, current booking seats open immediately.
A final chart is released ~30 min before departure.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.models.schemas import ChartWindow

IST = ZoneInfo("Asia/Kolkata")

# Window buffer (±minutes) around estimated chart time
CHART_WINDOW_BUFFER_MINUTES = 25


def _make_ist(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in IST."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def _parse_dep_time(dep_time_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' string into (hour, minute)."""
    parts = dep_time_str.strip().split(":")
    return int(parts[0]), int(parts[1])


def estimate_chart_window(
    journey_date: date,
    departure_time_str: str,
) -> tuple[ChartWindow, str, str, float]:
    """
    Estimate the first chart preparation window for a train.

    Args:
        journey_date: The date of travel (train departure date)
        departure_time_str: Departure time at origin station as 'HH:MM'

    Returns:
        (ChartWindow, rule_applied, notes, confidence)
    """
    dep_hour, dep_minute = _parse_dep_time(departure_time_str)

    # Build the full departure datetime in IST
    departure_dt = datetime(
        journey_date.year,
        journey_date.month,
        journey_date.day,
        dep_hour,
        dep_minute,
        tzinfo=IST,
    )

    # Convert to minutes from midnight for exact window routing
    dep_mins = dep_hour * 60 + dep_minute

    if 5 * 60 <= dep_mins <= 14 * 60:
        # Rule 1: Departs 05:00–14:00 → chart at 20:00 the PREVIOUS night
        prev_day = journey_date - timedelta(days=1)
        chart_center = datetime(prev_day.year, prev_day.month, prev_day.day, 20, 0, tzinfo=IST)
        rule = "Departure 05:00–14:00 → Chart by 20:00 prev. night (IRCTC 2025-26)"
        notes = (
            f"Trains departing between 5 AM and 2 PM are charted by 8 PM "
            f"the previous evening. This is an earlier charting rule introduced "
            f"by Indian Railways in 2025 to benefit passengers."
        )
        confidence = 0.82

    elif 14 * 60 < dep_mins <= 23 * 60 + 59:
        # Rule 2: Departs 14:01–23:59 → chart ~10 hours before
        chart_center = departure_dt - timedelta(hours=10)
        rule = "Departure 14:01–23:59 → Chart ~10 hours before departure (IRCTC 2025-26)"
        notes = (
            f"Trains departing in the afternoon/evening are charted approximately "
            f"10 hours before departure time. This rule replaced the older 8-hour "
            f"rule introduced via Railway Board directive in 2025."
        )
        confidence = 0.75

    else:
        # Rule 3: Departs 00:00–04:59 → chart ~10 hours before (previous afternoon)
        chart_center = departure_dt - timedelta(hours=10)
        rule = "Departure 00:00–04:59 → Chart ~10 hours before (often prev. evening)"
        notes = (
            f"For very early morning or late-night trains, the chart is prepared "
            f"approximately 10 hours prior, which often falls during the previous "
            f"afternoon or evening. Some such trains may still follow the older "
            f"'previous evening ~20:00' rule."
        )
        confidence = 0.68

    buffer = timedelta(minutes=CHART_WINDOW_BUFFER_MINUTES)
    window = ChartWindow(
        earliest=chart_center - buffer,
        latest=chart_center + buffer,
    )

    return window, rule, notes, confidence


def format_ist_time(dt: datetime) -> str:
    """Format a datetime as a human-readable IST string."""
    ist_dt = _make_ist(dt)
    return ist_dt.strftime("%I:%M %p IST, %d %b %Y")


def get_disclaimer() -> str:
    return (
        "This is an estimated window based on official IRCTC charting rules "
        "(Railway Board directives, 2025-26). Actual chart preparation may vary "
        "by 15–60 minutes. Always verify availability at the station counter "
        "or IRCTC app. This app is not affiliated with Indian Railways or IRCTC."
    )
