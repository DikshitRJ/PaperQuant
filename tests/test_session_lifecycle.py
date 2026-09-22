import asyncio

import pytest

session_module = pytest.importorskip("api.services.session_manager")


class FakeProcessManager:
    def __init__(self, *args, **kwargs):
        self.started = []
        self.stopped = False
        self.processes = {}

    def start_price_adapter(self):
        self.started.append("price_adapter")
        self.processes["price_adapter"] = object()

    def start_trade_adapter(self):
        self.started.append("trade_adapter")
        self.processes["trade_adapter"] = object()

    def start_strategy(self, *args):
        self.started.append("strategy")
        return True

    def stop_all(self):
        self.stopped = True
        self.processes = {}

    def get_status(self, name):
        return "running" if name in self.processes else "stopped"


class FakePortfolio:
    def get_enriched_positions(self):
        return []

    def get_aggregate_stats(self, start_time, active_algos=0):
        return {
            "session": {
                "pnl": "+$0.00",
                "invested": "$0.00",
                "current": "$0.00",
                "uptime": "00:00:00",
                "trend": "none",
            },
            "global": {
                "total_pnl": "+$0.00",
                "pnl_percent": "+0.00%",
                "active_algos": str(active_algos),
                "algo_runtime": "0h 0m",
                "pnl_trend": "none",
            },
        }


class FakeAlgorithmStore:
    def get(self, algorithm_id):
        return None

    def get_script_path(self, algorithm_id):
        return None


class FakeSettingsStore:
    def update(self, updates):
        return {}


class FakeStatsTracker:
    def clear(self):
        return None


def test_session_manager_rejects_second_start_without_spawning_more_processes(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(session_module, "ProcessManager", FakeProcessManager)
    monkeypatch.setattr(
        session_module, "PortfolioService", lambda *args: FakePortfolio()
    )
    monkeypatch.setattr(
        session_module, "AlgorithmStore", lambda *args: FakeAlgorithmStore()
    )
    monkeypatch.setattr(
        session_module, "SettingsStore", lambda *args: FakeSettingsStore()
    )
    monkeypatch.setattr(session_module, "StatsTracker", FakeStatsTracker)
    manager = session_module.SessionManager(base_dir=tmp_path)

    async def run():
        first = await manager.start_session([{"ticker": "AAPL", "capital": 1000}])
        with pytest.raises(RuntimeError):
            await manager.start_session([{"ticker": "MSFT", "capital": 1000}])
        return first

    first = asyncio.run(run())

    assert first["watchlist"] == ["AAPL"]
    assert manager.pm.started == ["price_adapter", "trade_adapter"]
    asyncio.run(manager.stop_session())


def test_stop_without_active_session_raises(monkeypatch):
    monkeypatch.setattr(session_module, "ProcessManager", FakeProcessManager)
    monkeypatch.setattr(
        session_module, "PortfolioService", lambda *args: FakePortfolio()
    )
    monkeypatch.setattr(
        session_module, "AlgorithmStore", lambda *args: FakeAlgorithmStore()
    )
    monkeypatch.setattr(
        session_module, "SettingsStore", lambda *args: FakeSettingsStore()
    )
    monkeypatch.setattr(session_module, "StatsTracker", FakeStatsTracker)
    manager = session_module.SessionManager()

    with pytest.raises(RuntimeError):
        asyncio.run(manager.stop_session())
