from fastapi import APIRouter, Request
from ..config import VERSION

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    manager = request.app.state.session_manager
    return {"status": "ok", "version": VERSION, "uptime_seconds": int(__import__("time").time() - request.app.state.started_at),
            "adapters": {"price_adapter": manager.process_manager.get_status("price_adapter"),
                         "trade_adapter": manager.process_manager.get_status("trade_adapter")}}

