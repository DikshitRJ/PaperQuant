import asyncio

import pytest


session_module = pytest.importorskip("api.services.session_manager")


class FakeProcessManager:
    def __init__(self, *args, **kwargs):
        self.started = []
        self.stopped = False

    def start_price_adapter(self):
        self.started.append("price_adapter")

    def start_trade_adapter(self):
        self.started.append("trade_adapter")

    def start_strategy(self, *args):
        self.started.append("strategy")

    def stop_all(self):
        self.stopped = True


class FakePortfolio:
    def get_enriched_positions(self):
        return []

    def get_aggregate_stats(self, start_time):
        return {"session": {}, "global": {}}


class FakeAlgorithmStore:
    def get_script_path(self, algorithm_id):
        return None


class FakeSettingsStore:
    pass


class FakeStatsTracker:
    pass


def test_session_manager_rejects_second_start_without_spawning_more_processes(monkeypatch, tmp_path):
    monkeypatch.setattr(session_module, "ProcessManager", FakeProcessManager)
    monkeypatch.setattr(session_module, "PortfolioService", lambda *args: FakePortfolio())
    monkeypatch.setattr(session_module, "AlgorithmStore", lambda *args: FakeAlgorithmStore())
    monkeypatch.setattr(session_module, "SettingsStore", lambda *args: FakeSettingsStore())
    monkeypatch.setattr(session_module, "StatsTracker", FakeStatsTracker)
    manager = session_module.SessionManager()
    manager.base_dir = str(tmp_path)
    manager.temp_dir = str(tmp_path / "Temporary")

    async def run():
        first = await manager.start_session([{"ticker": "AAPL", "capital": 1000}])
        second = await manager.start_session([{"ticker": "MSFT", "capital": 1000}])
        return first, second

    first, second = asyncio.run(run())

    assert first["watchlist"] == ["AAPL"]
    assert second is None
    assert manager.pm.started == ["price_adapter", "trade_adapter"]
    asyncio.run(manager.stop_session())


def test_stop_without_active_session_is_noop(monkeypatch):
    monkeypatch.setattr(session_module, "ProcessManager", FakeProcessManager)
    monkeypatch.setattr(session_module, "PortfolioService", lambda *args: FakePortfolio())
    monkeypatch.setattr(session_module, "AlgorithmStore", lambda *args: FakeAlgorithmStore())
    monkeypatch.setattr(session_module, "SettingsStore", lambda *args: FakeSettingsStore())
    monkeypatch.setattr(session_module, "StatsTracker", FakeStatsTracker)
    manager = session_module.SessionManager()

    assert asyncio.run(manager.stop_session()) is None
