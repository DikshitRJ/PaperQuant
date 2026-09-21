import os
import sys
import webview
import subprocess
import threading
import json
import time
import shutil
from datetime import datetime
from diskcache import Cache

# -------------------------------------------------
# Configuration
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = os.path.join(BASE_DIR, "UI", "Frontend", "dist")
PYTHON_EXE = os.path.join(BASE_DIR, ".venv", "bin", "python")

STATE_CACHE_PATH = os.path.join(BASE_DIR, "Temporary", "state")
LOG_HISTORY_SIZE = 100

# -------------------------------------------------
# Log Capture
# -------------------------------------------------

class LogBuffer:
    def __init__(self, size=100):
        self.buffer = []
        self.size = size
        self.lock = threading.Lock()

    def add(self, source, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{source}] {message.strip()}"
        with self.lock:
            self.buffer.append(line)
            if len(self.buffer) > self.size:
                self.buffer.pop(0)

    def get_all(self):
        with self.lock:
            return list(self.buffer)

log_buffer = LogBuffer(LOG_HISTORY_SIZE)

# -------------------------------------------------
# Subprocess Management
# -------------------------------------------------

class ProcessManager:
    def __init__(self):
        self.processes = {}

    def start_process(self, name, cmd, cwd=BASE_DIR):
        if name in self.processes and self.processes[name].poll() is None:
            log_buffer.add("SYSTEM", f"{name} is already running.")
            return

        log_buffer.add("SYSTEM", f"Starting {name}...")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd,
                bufsize=1,
                universal_newlines=True
            )
            self.processes[name] = proc
            threading.Thread(target=self._read_output, args=(name, proc), daemon=True).start()
        except Exception as e:
            log_buffer.add("SYSTEM", f"Failed to start {name}: {e}")

    def _read_output(self, name, proc):
        for line in iter(proc.stdout.readline, ""):
            log_buffer.add(name, line)
        proc.stdout.close()
        return_code = proc.wait()
        log_buffer.add("SYSTEM", f"{name} exited with code {return_code}")

    def stop_all(self):
        for name, proc in self.processes.items():
            if proc.poll() is None:
                log_buffer.add("SYSTEM", f"Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

pm = ProcessManager()

# -------------------------------------------------
# API exposed to Frontend
# -------------------------------------------------

class API:
    def __init__(self):
        self._window = None
        self._polling = False

    def set_window(self, window):
        self._window = window
        self._polling = True
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        while self._polling:
            if self._window:
                try:
                    # Sync Logs
                    logs = self.get_logs()
                    # We pass the list of strings. The frontend expects LogEntry objects usually, 
                    # but let's check what addLog expects.
                    # Based on context, it looks like it might expect a string or an object.
                    # If it's the global addLog exposed in PaperQuantContext.tsx:
                    # (window as any).addLog = addLog;
                    # It might need formatting. For now, let's just clear and set if possible, 
                    # or just call a JS helper.
                    
                    # More robust: push state
                    positions = self.get_positions()
                    self._window.evaluate_js(f"if(window.updatePositions) window.updatePositions({json.dumps(positions)})")
                    
                    # For logs, it's better to only send NEW logs, but for a prototype, we can send all or handle it in JS.
                    # Let's just send the latest logs.
                    self._window.evaluate_js(f"if(window.clearLogs) window.clearLogs()")
                    for log in logs:
                        # Convert string to LogEntry-like object if needed, or just string
                        # UI components usually expect {id, type, message, timestamp}
                        log_obj = {"id": hash(log), "message": log, "timestamp": "", "type": "info"}
                        self._window.evaluate_js(f"if(window.addLog) window.addLog({json.dumps(log_obj)})")

                except Exception as e:
                    print(f"Polling error: {e}")
            time.sleep(2)

    def reset_session(self):
        log_buffer.add("SYSTEM", "Resetting session...")
        pm.stop_all()
        
        # Clear temporary data
        temp_dir = os.path.join(BASE_DIR, "Temporary")
        for item in os.listdir(temp_dir):
            if item == "stocklist.json": continue # Keep stocklist
            path = os.path.join(temp_dir, item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                log_buffer.add("SYSTEM", f"Error clearing {item}: {e}")
        
        # Recreate state dir
        os.makedirs(STATE_CACHE_PATH, exist_ok=True)
        
        # Restart adapters
        self.start_adapters()
        return {"status": "ok"}

    def stop_session(self):
        log_buffer.add("SYSTEM", "Stopping all services...")
        pm.stop_all()
        return {"status": "ok"}

    def get_positions(self):
        try:
            cache = Cache(STATE_CACHE_PATH)
            positions = []
            for key in cache.iterkeys():
                data = cache.get(key)
                # Key format is "strategy_id:symbol"
                if ":" in key:
                    strat_id, symbol = key.split(":")
                    if isinstance(data, dict):
                        positions.append({
                            "strategy_id": strat_id,
                            "symbol": symbol,
                            "qty": data.get("qty", 0),
                            "avg_price": data.get("avg_price", 0.0)
                        })
            cache.close()
            return positions
        except Exception as e:
            log_buffer.add("SYSTEM", f"Error getting positions: {e}")
            return []

    def get_logs(self):
        return log_buffer.get_all()

    def start_adapters(self):
        # Start Price Adapter
        pm.start_process("PRICE", [PYTHON_EXE, "Price_adapter/main.py"])
        # Start Trade Adapter
        pm.start_process("TRADE", [PYTHON_EXE, "Trade_adapter.py"])

# -------------------------------------------------
# Main Entry
# -------------------------------------------------

def main():
    if not os.path.exists(DIST_DIR):
        print(f"Error: {DIST_DIR} not found. Build the frontend first.")
        sys.exit(1)

    api = API()
    
    # Pre-start adapters
    api.start_adapters()

    window = webview.create_window(
        "PaperQuant Desktop",
        url=os.path.join(DIST_DIR, "index.html"),
        js_api=api,
        width=1280,
        height=800
    )
    api.set_window(window)

    try:
        webview.start(debug=True)
    finally:
        pm.stop_all()

if __name__ == "__main__":
    main()
