from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = Path(os.getenv("PAPERQUANT_TEMP_DIR", BASE_DIR / "Temporary"))
ALGORITHMS_DIR = Path(os.getenv("PAPERQUANT_ALGORITHMS_DIR", BASE_DIR / "algorithms"))
CONFIG_DIR = Path(os.getenv("PAPERQUANT_CONFIG_DIR", Path.home() / ".paperquant"))
STATE_CACHE_PATH = TEMP_DIR / "state"
LIVE_PRICES_CACHE_PATH = TEMP_DIR / "cache_liveprices"
ORDER_HISTORY_PATH = TEMP_DIR / "order_history.csv"
DATABASE_PATH = TEMP_DIR / "paperquant.db"
VERSION = "0.2.0"

for _path in (TEMP_DIR, ALGORITHMS_DIR, CONFIG_DIR):
    _path.mkdir(parents=True, exist_ok=True)

