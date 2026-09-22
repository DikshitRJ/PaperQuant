from __future__ import annotations

import asyncio
import csv
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import CONFIG_DIR
from .algorithm_store import AlgorithmStore
from .log_buffer import LogBuffer
from .portfolio import PortfolioService
from .process_manager import ProcessManager
from .settings_store import SettingsStore
from .stats_tracker import StatsTracker


class SessionManager:
    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parents[2])
        self.temp_dir = self.base_dir / "Temporary"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.state_cache_path = self.temp_dir / "state"
        self.live_prices_cache_path = self.temp_dir / "cache_liveprices"
        self.order_history_path = self.temp_dir / "order_history.csv"
        self.database_path = self.temp_dir / "paperquant.db"
        self.algorithms_dir = self.base_dir / "algorithms"
        self.state_cache_path.mkdir(parents=True, exist_ok=True)
        self.live_prices_cache_path.mkdir(parents=True, exist_ok=True)
        self.algorithms_dir.mkdir(parents=True, exist_ok=True)
        self.log_buffer = LogBuffer()
        self.process_manager = ProcessManager(self.base_dir, self.log_buffer)
        self.pm = self.process_manager
        self.portfolio = PortfolioService(self.state_cache_path, self.live_prices_cache_path)
        self.algorithm_store = AlgorithmStore(self.base_dir, self.database_path)
        self.settings = SettingsStore(CONFIG_DIR)
        self.stats_tracker = StatsTracker()
        self.active_session: dict | None = None
        self.start_time: float | None = None
        self._push_task: asyncio.Task | None = None
        self._last_log_count = 0
        self._last_trade_count = 0
        self._last_chart_push = 0.0
        self._last_price_tick: dict[str, float] = {}
        self._last_adapter_status: dict[str, str] = {}

    async def initialize(self) -> None:
        self.log_buffer.add("system", "PaperQuant API server initialized")

    async def shutdown(self) -> None:
        if self._push_task:
            self._push_task.cancel()
            try:
                await self._push_task
            except asyncio.CancelledError:
                pass
        self.process_manager.stop_all()

    async def start_session(self, watchlist: list[dict], strategy_id: str | None = None,
                            session_settings: dict | None = None) -> dict:
        if self.active_session:
            raise RuntimeError("session_active")
        self.settings.update(session_settings or {})
        tickers = [item["ticker"].upper() for item in watchlist]
        (self.temp_dir / "stocklist.json").write_text(json.dumps(tickers))
        self.process_manager.start_price_adapter()
        self.process_manager.start_trade_adapter()
        self.start_time = time.time()
        session_id = f"sess_{time.strftime('%Y%m%d_%H%M%S')}"
        self.active_session = {"session_id": session_id, "started_at": datetime.now(timezone.utc).isoformat(),
                               "watchlist": tickers, "strategy_id": strategy_id}
        if strategy_id:
            script = self.algorithm_store.get_script_path(strategy_id)
            if not script:
                self.process_manager.stop_all()
                self.active_session = None
                self.start_time = None
                raise RuntimeError("algorithm_not_found")
            for ticker in tickers:
                self.process_manager.start_strategy(strategy_id, script, ticker)
        self._push_task = asyncio.create_task(self._push_loop())
        self._last_log_count = 0
        self._last_trade_count = len(self.history())
        self._last_chart_push = time.time()
        self.log_buffer.add("system", f"Session {session_id} started with {len(tickers)} tickers")
        await self._broadcast_adapter_status(force=True)
        return self.active_session

    async def stop_session(self) -> dict:
        if not self.active_session:
            raise RuntimeError("no_active_session")
        session, start = self.active_session, self.start_time
        from ..websocket import manager as ws_manager
        self.process_manager.stop_all()
        if self._push_task:
            self._push_task.cancel()
            self._push_task = None
        self.active_session = self.start_time = None
        self.log_buffer.add("system", f"Session {session['session_id']} stopped")
        await ws_manager.broadcast("session_ended", {"reason": "stopped_by_user"})
        await self._broadcast_adapter_status(force=True)
        return {"status": "stopped", "session_id": session["session_id"],
                "duration_seconds": int(time.time() - start) if start else 0}

    async def reset_session(self) -> dict:
        if self.active_session:
            await self.stop_session()
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        for item in self.temp_dir.iterdir():
            if item.name == "stocklist.json":
                item.write_text("[]")
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        for path in (self.state_cache_path, self.live_prices_cache_path, self.temp_dir / "cache_candles"):
            path.mkdir(parents=True, exist_ok=True)
        self.stats_tracker.clear()
        self.log_buffer.clear()
        self.process_manager.start_price_adapter()
        self.process_manager.start_trade_adapter()
        self.log_buffer.add("system", "Session reset complete")
        await self._broadcast_adapter_status(force=True)
        return {"status": "reset", "message": "Session data cleared and adapters restarted."}

    def status(self) -> dict:
        if not self.active_session:
            return {"active": False, "adapters": {"price_adapter": self.process_manager.get_status("price_adapter"),
                                                  "trade_adapter": self.process_manager.get_status("trade_adapter")}}
        strategy_id = self.active_session.get("strategy_id")
        strategy_name = strategy_id
        if strategy_id:
            algo = self.algorithm_store.get(strategy_id)
            if algo:
                strategy_name = algo.get("name", strategy_id)
        result = {**self.active_session, "active": True, "uptime_seconds": int(time.time() - (self.start_time or time.time())),
                 "strategy": {"id": strategy_id, "name": strategy_name,
                              "status": "running" if self.active_session.get("strategy_id") else "stopped"},
                 "adapters": {"price_adapter": self.process_manager.get_status("price_adapter"),
                              "trade_adapter": self.process_manager.get_status("trade_adapter")}}
        return result

    def history(self) -> list[dict]:
        if not self.order_history_path.exists():
            return []
        with self.order_history_path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        return [{"timestamp": r.get("Timestamp", ""), "strategy_id": r.get("Strategy_ID", ""),
                 "symbol": r.get("Symbol", ""), "side": r.get("Action", ""),
                 "qty": int(float(r.get("Executed_Quantity", 0))), "price": float(r.get("Executed_Price", 0)),
                 "order_type": "market"}
                for r in rows]

    async def _push_loop(self) -> None:
        from ..websocket import manager
        while True:
            try:
                positions = self.portfolio.get_enriched_positions()
                await manager.broadcast("positions_update", {"positions": positions})
                stats = self.portfolio.get_aggregate_stats(
                   self.start_time,
                   sum(1 for name in self.process_manager.processes if name.startswith("strategy_")),
                )
                await manager.broadcast("stats_update", stats)
                if stats["session"]["pnl"]:
                   numeric = float(stats["session"]["pnl"].replace("+", "").replace("$", "").replace(",", ""))
                   self.stats_tracker.record(numeric)
                logs = self.log_buffer.get_all()
                if len(logs) > self._last_log_count:
                   for entry in logs[self._last_log_count:]:
                       await manager.broadcast("log", entry)
                   self._last_log_count = len(logs)
                await self._broadcast_adapter_status()
                await self._broadcast_price_ticks()
                await self._broadcast_trade_events()
                if time.time() - self._last_chart_push >= 60:
                   await manager.broadcast("chart_update", self.stats_tracker.chart())
                   self._last_chart_push = time.time()
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.log_buffer.add("error", f"Push loop error: {exc}")
                await manager.broadcast("error", {"code": "internal_error", "message": str(exc)})
                await asyncio.sleep(5)

    async def _broadcast_adapter_status(self, force: bool = False) -> None:
        from ..websocket import manager
        current = {
            "price_adapter": self.process_manager.get_status("price_adapter"),
            "trade_adapter": self.process_manager.get_status("trade_adapter"),
        }
        for adapter, status in current.items():
            if force or self._last_adapter_status.get(adapter) != status:
                await manager.broadcast("adapter_status", {"adapter": adapter, "status": status})
        self._last_adapter_status = current

    async def _broadcast_price_ticks(self) -> None:
        from ..websocket import manager
        now = time.time()
        for key in self.portfolio.prices_cache.iterkeys():
            key_str = str(key)
            if not key_str.startswith("prices:"):
                continue
            symbol = key_str.split(":", 1)[1]
            values = self.portfolio.prices_cache.get(key, [])
            if not values:
                continue
            last_sent = self._last_price_tick.get(symbol, 0.0)
            if now - last_sent < 1:
                continue
            latest = values[-1]
            if not isinstance(latest, dict) or "price" not in latest:
                continue
            await manager.broadcast("price_tick", {"symbol": symbol, "price": float(latest["price"]), "ts": latest.get("ts")})
            self._last_price_tick[symbol] = now

    async def _broadcast_trade_events(self) -> None:
        from ..websocket import manager
        trades = self.history()
        if len(trades) <= self._last_trade_count:
            return
        for trade in trades[self._last_trade_count:]:
            await manager.broadcast(
                "trade_executed",
                {"symbol": trade["symbol"], "side": trade["side"], "qty": trade["qty"], "price": trade["price"]},
            )
        self._last_trade_count = len(trades)
