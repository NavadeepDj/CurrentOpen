"""
RailChart — FastAPI Application Entry Point

Run with: uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.chart import router as chart_router

app = FastAPI(
    title="RailChart API",
    description=(
        "Estimates the first reservation chart preparation window for Indian trains, "
        "so passengers know when Current Booking tickets become available at station counters."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow frontend served from any origin (for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "RailChart API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
