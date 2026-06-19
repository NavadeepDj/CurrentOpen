"""
RailChart Backend — Pydantic schemas for request/response
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChartEstimateRequest(BaseModel):
    train_number: str = Field(..., description="Train number e.g. '12617'")
    journey_date: date = Field(..., description="Journey date in YYYY-MM-DD format")


class ChartWindow(BaseModel):
    earliest: datetime = Field(..., description="Earliest expected chart preparation time (IST)")
    latest: datetime = Field(..., description="Latest expected chart preparation time (IST)")


class TrainInfo(BaseModel):
    train_number: str
    train_name: str
    origin_station_code: str
    origin_station_name: str
    origin_departure_time: str  # HH:MM


class ChartEstimateResponse(BaseModel):
    train_number: str
    train_name: str
    journey_date: date
    origin_station: str
    origin_departure_time: str
    first_chart_window: ChartWindow
    current_booking_opens: datetime
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: Literal["heuristic", "historical"]
    rule_applied: str
    notes: str
    disclaimer: str


class TrainSearchResult(BaseModel):
    train_number: str
    train_name: str
    origin_station_code: str
    origin_station_name: str
    departure_time: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
