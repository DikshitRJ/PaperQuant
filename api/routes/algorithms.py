from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from ..schemas import AlgorithmRunRequest
from ..websocket import manager as ws_manager

router = APIRouter(prefix="/algorithms")


@router.get("")
async def list_algorithms(request: Request):
    return {
        "algorithms": request.app.state.session_manager.algorithm_store.list_algorithms()
    }


@router.post("")
async def register(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    dependencies: str = Form(""),
):
    manager = request.app.state.session_manager
    if not file.filename or not file.filename.endswith(".py"):
        return JSONResponse(
            status_code=400,
            content={"error": "file_invalid", "message": "Upload a Python script."},
        )
    try:
        result = manager.algorithm_store.register(
            name,
            file.filename,
            [x.strip() for x in dependencies.split(",") if x.strip()],
            await file.read(),
        )
        return JSONResponse(status_code=201, content=result)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={
                "error": "file_invalid",
                "message": "Invalid Python script filename.",
            },
        )


@router.delete("/{algorithm_id}")
async def delete(algorithm_id: str, request: Request):
    manager = request.app.state.session_manager
    if not manager.algorithm_store.delete(algorithm_id):
        return JSONResponse(
            status_code=404,
            content={"error": "algorithm_not_found", "message": "Algorithm not found."},
        )
    return {"status": "deleted", "id": algorithm_id}


@router.post("/{algorithm_id}/run")
async def run(algorithm_id: str, payload: AlgorithmRunRequest, request: Request):
    manager = request.app.state.session_manager
    algo = manager.algorithm_store.get(algorithm_id)
    if not algo:
        return JSONResponse(
            status_code=404,
            content={"error": "algorithm_not_found", "message": "Algorithm not found."},
        )
    if not manager.active_session:
        return JSONResponse(
            status_code=400,
            content={"error": "no_active_session", "message": "Start a session first."},
        )
    started = manager.process_manager.start_strategy(
        algorithm_id,
        manager.algorithm_store.get_script_path(algorithm_id),
        payload.symbol.upper(),
    )
    if not started:
        return JSONResponse(
            status_code=409,
            content={
                "error": "algorithm_already_running",
                "message": "Algorithm is already running.",
            },
        )
    run = manager.algorithm_store.start_run(algorithm_id)
    await ws_manager.broadcast(
        "strategy_update", {"name": algo["name"], "status": "running"}
    )
    return {
        "status": "started",
        "run_id": run["run_id"],
        "algorithm_id": algorithm_id,
        "symbol": payload.symbol.upper(),
    }


@router.post("/{algorithm_id}/stop")
async def stop(algorithm_id: str, request: Request):
    manager = request.app.state.session_manager
    algo = manager.algorithm_store.get(algorithm_id)
    if not algo:
        return JSONResponse(
            status_code=404,
            content={"error": "algorithm_not_found", "message": "Algorithm not found."},
        )
    names = [
        name
        for name in manager.process_manager.processes
        if name.startswith(f"strategy_{algorithm_id}_")
    ]
    for name in names:
        manager.process_manager.stop_process(name)
    run = manager.algorithm_store.find_active_run(algorithm_id)
    run_id = run["run_id"] if run else f"run_{algorithm_id}"
    if run:
        manager.algorithm_store.finish_run(run_id, status="Stopped")
    await ws_manager.broadcast(
        "strategy_update", {"name": algo["name"], "status": "stopped"}
    )
    return {"status": "stopped", "run_id": run_id}
