from fastapi import APIRouter, Request

from ..schemas import SettingsUpdate

router = APIRouter()


@router.get("/settings")
async def get_settings(request: Request):
    return request.app.state.session_manager.settings.get_all()


@router.put("/settings")
async def update_settings(request: Request, payload: SettingsUpdate):
    settings = request.app.state.session_manager.settings.update(
        payload.model_dump(exclude_none=True)
    )
    return {"status": "updated", "settings": settings}
