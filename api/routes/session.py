from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..schemas import SessionStartRequest

router = APIRouter(prefix="/session")


def error(code: str, message: str, status: int):
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@router.post("/start")
async def start(request: Request, payload: SessionStartRequest):
    manager = request.app.state.session_manager
    try:
        session = await manager.start_session(
            [item.model_dump() for item in payload.watchlist],
            payload.strategy_id,
            payload.settings,
        )
    except RuntimeError as exc:
        code = str(exc)
        if code == "algorithm_not_found":
            return error(code, "The requested algorithm does not exist.", 404)
        return error(code, "A session is already running. Stop it first.", 409)
    return {"status": "started", **session}


@router.post("/stop")
async def stop(request: Request):
    try:
        return await request.app.state.session_manager.stop_session()
    except RuntimeError:
        return error("no_active_session", "No session is currently running.", 400)


@router.post("/reset")
async def reset(request: Request):
    return await request.app.state.session_manager.reset_session()


@router.get("/status")
async def status(request: Request):
    return request.app.state.session_manager.status()
