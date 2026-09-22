from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    capital: float = Field(default=1000.0, gt=0)


class SessionStartRequest(BaseModel):
    watchlist: list[WatchlistItem] = Field(min_length=1)
    strategy_id: str | None = None
    settings: dict[str, Any] | None = None


class AlgorithmRunRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)


class Position(BaseModel):
    ticker: str
    initials: str
    qty: int
    avg_price: float
    current_price: float
    invested: str
    current: str
    pnl: str
    pnl_percent: str
    strategy_id: str


class Trade(BaseModel):
    timestamp: str
    strategy_id: str
    symbol: str
    side: str
    qty: int
    price: float
    order_type: str = "market"


class AlgorithmRun(BaseModel):
    run_id: str
    date: str
    pnl: str
    status: str
    duration_seconds: int


class Algorithm(BaseModel):
    id: str
    name: str
    filename: str
    dependencies: list[str]
    created_at: str
    history: list[AlgorithmRun] = Field(default_factory=list)


Trend = Literal["up", "down", "none"]


class SessionStats(BaseModel):
    pnl: str
    invested: str
    current: str
    uptime: str
    trend: Trend


class GlobalStats(BaseModel):
    total_pnl: str
    pnl_percent: str
    active_algos: str
    algo_runtime: str
    pnl_trend: Trend


class Settings(BaseModel):
    currency: Literal["USD", "EUR", "GBP", "INR"] = "USD"
    theme: str = "dark"
    simulated_latency_ms: int = Field(default=0, ge=0)
    commission_percent: float = Field(default=0.0, ge=0)
    leverage: int = Field(default=1, ge=1)
    auto_clear_logs: bool = True
    system_alerts: bool = True
    sound_effects: bool = False
    terminal_font_size: int = Field(default=14, ge=8, le=32)


class SettingsUpdate(BaseModel):
    currency: Literal["USD", "EUR", "GBP", "INR"] | None = None
    theme: str | None = None
    simulated_latency_ms: int | None = Field(default=None, ge=0)
    commission_percent: float | None = Field(default=None, ge=0)
    leverage: int | None = Field(default=None, ge=1)
    auto_clear_logs: bool | None = None
    system_alerts: bool | None = None
    sound_effects: bool | None = None
    terminal_font_size: int | None = Field(default=None, ge=8, le=32)

