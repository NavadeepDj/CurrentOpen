"""
RailChart — Chart Estimate Router
"""

from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    ChartEstimateRequest,
    ChartEstimateResponse,
    ErrorResponse,
    TrainSearchResult,
)
from backend.services.heuristic import estimate_chart_window, get_disclaimer
from backend.services.train_lookup import get_train_info, search_trains

router = APIRouter(prefix="/api", tags=["chart"])


@router.post(
    "/chart-estimate",
    response_model=ChartEstimateResponse,
    summary="Get first chart preparation window for a train",
)
async def chart_estimate(req: ChartEstimateRequest) -> ChartEstimateResponse:
    """
    Given a train number and journey date, return the estimated
    first reservation chart preparation window and current booking opening time.
    """
    # 1. Look up train info
    train = get_train_info(req.train_number)
    if train is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train '{req.train_number}' not found in the timetable database. "
                   f"Try searching via /api/trains/search?q={req.train_number}",
        )

    # 2. Validate journey date is not in the past
    today = date.today()
    if req.journey_date < today:
        raise HTTPException(
            status_code=422,
            detail=f"Journey date {req.journey_date} is in the past. "
                   f"Please provide a future or today's journey date.",
        )

    # 3. Estimate chart window
    chart_window, rule, notes, confidence = estimate_chart_window(
        journey_date=req.journey_date,
        departure_time_str=train.origin_departure_time,
    )

    return ChartEstimateResponse(
        train_number=train.train_number,
        train_name=train.train_name,
        journey_date=req.journey_date,
        origin_station=f"{train.origin_station_name} ({train.origin_station_code})",
        origin_departure_time=train.origin_departure_time,
        first_chart_window=chart_window,
        current_booking_opens=chart_window.earliest,
        confidence=confidence,
        method="heuristic",
        rule_applied=rule,
        notes=notes,
        disclaimer=get_disclaimer(),
    )


@router.get(
    "/trains/search",
    response_model=List[TrainSearchResult],
    summary="Search trains by number or name",
)
async def search_trains_endpoint(
    q: str = Query(..., description="Train number prefix or name keyword", min_length=2),
    limit: int = Query(10, ge=1, le=30),
) -> List[TrainSearchResult]:
    """
    Search for trains by number (prefix) or name (keyword).
    Returns matching train entries from the static dataset.
    """
    results = search_trains(q, limit=limit)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No trains found matching '{q}'",
        )
    return results


@router.get(
    "/trains/{train_number}",
    response_model=TrainSearchResult,
    summary="Get train info by number",
)
async def get_train(train_number: str) -> TrainSearchResult:
    """
    Get train info for a specific train number.
    """
    train = get_train_info(train_number)
    if train is None:
        raise HTTPException(status_code=404, detail=f"Train '{train_number}' not found")
    return TrainSearchResult(
        train_number=train.train_number,
        train_name=train.train_name,
        origin_station_code=train.origin_station_code,
        origin_station_name=train.origin_station_name,
        departure_time=train.origin_departure_time,
    )
