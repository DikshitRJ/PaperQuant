from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/logs")
async def logs(request: Request, since: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=1000)):
    return {"logs": request.app.state.session_manager.log_buffer.get_since(since, limit)}

