from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections.abc import Mapping
from pathlib import Path

from .log_buffer import LogBuffer


class ProcessManager:
    def __init__(self, base_dir: str | Path, log_buffer: LogBuffer):
        self.base_dir = Path(base_dir)
        self.log_buffer = log_buffer
        self.processes: dict[str, subprocess.Popen[str]] = {}
        self._lock = threading.Lock()

    def start_process(
        self,
        name: str,
        cmd: list[str],
        cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> bool:
        with self._lock:
            existing = self.processes.get(name)
            if existing and existing.poll() is None:
                return False
            full_env = os.environ.copy()
            if env:
                full_env.update(env)
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd or self.base_dir),
                env=full_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.processes[name] = proc
        threading.Thread(
            target=self._read_output, args=(name, proc), daemon=True
        ).start()
        return True

    def start_price_adapter(self) -> bool:
        return self.start_process(
            "price_adapter",
            [sys.executable, "main.py"],
            self.base_dir / "Price_adapter",
        )

    def start_trade_adapter(self) -> bool:
        return self.start_process("trade_adapter", [sys.executable, "Trade_adapter.py"])

    def start_strategy(
        self,
        strategy_id: str,
        script_path: str | Path,
        symbol: str,
        trade_endpoint: str = "tcp://127.0.0.1:5555",
    ) -> bool:
        env = {
            "SIM_STRATEGY_ID": strategy_id,
            "SIM_SYMBOL": symbol,
            "SIM_TRADE_ENDPOINT": trade_endpoint,
            "SIM_CACHE_PATH": str(self.base_dir / "Temporary" / "cache_candles"),
        }
        return self.start_process(
            f"strategy_{strategy_id}_{symbol}",
            [sys.executable, str(script_path)],
            env=env,
        )

    def get_status(self, name: str) -> str:
        proc = self.processes.get(name)
        if proc is None:
            return "stopped"
        return "running" if proc.poll() is None else "error"

    def stop_process(self, name: str) -> None:
        proc = self.processes.pop(name, None)
        if not proc or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

    def stop_all(self) -> None:
        for name in list(self.processes):
            self.stop_process(name)

    def _read_output(self, name: str, proc: subprocess.Popen[str]) -> None:
        if proc.stdout is None:
            return
        try:
            for line in proc.stdout:
                self.log_buffer.add(
                    name if name in self.log_buffer.SOURCE_COLORS else "strategy", line
                )
        finally:
            proc.stdout.close()
