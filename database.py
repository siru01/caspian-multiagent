"""
database.py

Lightweight JSON-backed persistence for the Caspian Agent.
Swap this out for a real database (SQLite/Postgres) once you outgrow flat files.
"""

import json
import os
from datetime import datetime, timezone
from threading import Lock

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ANALYTICS_PATH = os.path.join(DATA_DIR, "analytics.json")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

_lock = Lock()


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def _write_json(path, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_settings():
    return _read_json(SETTINGS_PATH, {})


def update_settings(new_settings: dict):
    with _lock:
        settings = get_settings()
        settings.update(new_settings)
        _write_json(SETTINGS_PATH, settings)
        return settings


def log_message(user_query: str, reply: str, channel: str = "unknown"):
    """Append a message exchange to analytics.json for later review."""
    with _lock:
        analytics = _read_json(ANALYTICS_PATH, {"messages": []})
        analytics["messages"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "query": user_query,
            "reply": reply,
        })
        _write_json(ANALYTICS_PATH, analytics)


def get_analytics():
    return _read_json(ANALYTICS_PATH, {"messages": []})
