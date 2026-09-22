from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from diskcache import Cache
except ImportError:  # pragma: no cover
    Cache = None


class PortfolioService:
    def __init__(self, state_cache_path: str | Path, liveprices_cache_path: str | Path):
        if Cache is None:
            raise RuntimeError("diskcache is required to use PortfolioService")
        self.state_cache = Cache(str(state_cache_path))
        self.prices_cache = Cache(str(liveprices_cache_path))

    def get_current_price(self, symbol: str) -> float | None:
        prices = self.prices_cache.get(f"prices:{symbol}", [])
        return float(prices[-1]["price"]) if prices and isinstance(prices[-1], dict) else None

    def get_enriched_positions(self) -> list[dict[str, Any]]:
        positions = []
        for key in self.state_cache.iterkeys():
            if ":" not in str(key):
                continue
            strategy_id, symbol = str(key).split(":", 1)
            data = self.state_cache.get(key)
            if not isinstance(data, dict) or not data.get("qty"):
                continue
            qty, avg = int(data["qty"]), float(data.get("avg_price", 0))
            current = self.get_current_price(symbol)
            if current is None:
                current = avg
            invested, value = abs(qty) * avg, abs(qty) * current
            pnl = (value - invested) * (1 if qty > 0 else -1)
            pct = pnl / invested * 100 if invested else 0
            positions.append({
                "ticker": symbol, "initials": symbol[:2].upper(), "qty": qty,
                "avg_price": round(avg, 2), "current_price": round(current, 2),
                "invested": f"${invested:,.2f}", "current": f"${value:,.2f}",
                "pnl": f"{'+' if pnl >= 0 else '-'}${abs(pnl):,.2f}",
                "pnl_percent": f"{'+' if pct >= 0 else '-'}{abs(pct):.2f}%",
                "strategy_id": strategy_id,
            })
        return positions

    def get_aggregate_stats(self, session_start_time: float | None, active_algos: int = 0) -> dict:
        import time
        positions = self.get_enriched_positions()
        invested = sum(float(p["invested"].replace("$", "").replace(",", "")) for p in positions)
        current = sum(float(p["current"].replace("$", "").replace(",", "")) for p in positions)
        pnl = current - invested
        pct = pnl / invested * 100 if invested else 0
        elapsed = max(0, int(time.time() - session_start_time)) if session_start_time else 0
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        trend = "up" if pnl > 0 else "down" if pnl < 0 else "none"
        money = lambda n: f"{'+' if n >= 0 else '-'}${abs(n):,.2f}"
        return {
            "session": {"pnl": money(pnl), "invested": f"${invested:,.2f}", "current": f"${current:,.2f}",
                        "uptime": f"{h:02d}:{m:02d}:{s:02d}", "trend": trend},
            "global": {"total_pnl": money(pnl), "pnl_percent": f"{'+' if pct >= 0 else '-'}{abs(pct):.2f}%",
                       "active_algos": str(active_algos), "algo_runtime": f"{h}h {m}m", "pnl_trend": trend},
        }
