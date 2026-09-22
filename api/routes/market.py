from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

try:
    from diskcache import Cache
except ImportError:  # pragma: no cover
    Cache = None

router = APIRouter(prefix="/market")


@router.get("/prices")
async def prices(request: Request):
    if Cache is None:
        return {"prices": {}}
    cache = Cache(
        str(request.app.state.session_manager.portfolio.prices_cache.directory)
    )
    try:
        result = {}
        for key in cache.iterkeys():
            if str(key).startswith("prices:"):
                values = cache.get(key, [])
                if values:
                    latest = values[-1]
                    ts = latest.get("ts")
                    if isinstance(ts, (int, float)):
                        ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    result[str(key).split(":", 1)[1]] = {
                        "price": latest["price"],
                        "timestamp": ts,
                        "source": "live",
                    }
        return {"prices": result}
    finally:
        cache.close()
