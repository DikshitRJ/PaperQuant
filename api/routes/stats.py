from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/stats")
async def stats(request: Request):
    manager = request.app.state.session_manager
    return manager.portfolio.get_aggregate_stats(
        manager.start_time,
        sum(1 for name in manager.process_manager.processes if name.startswith("strategy_")),
    )


@router.get("/stats/chart")
async def chart(request: Request):
    return request.app.state.session_manager.stats_tracker.chart()
