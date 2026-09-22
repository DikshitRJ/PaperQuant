from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/positions")
async def positions(request: Request):
    return {"positions": request.app.state.session_manager.portfolio.get_enriched_positions()}


@router.get("/positions/history")
async def history(request: Request):
    return {"trades": request.app.state.session_manager.history()}

