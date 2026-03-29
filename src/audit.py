import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = Path("logs/audit.jsonl")


def log_event(action, status, username=None, role=None, details=None):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "status": status,
        "username": username,
        "role": role,
        "details": details or {},
    }

    with AUDIT_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry) + "\n")


def read_recent_logs(limit=50):
    if not AUDIT_LOG.exists():
        return []

    with AUDIT_LOG.open("r", encoding="utf-8") as log_file:
        lines = [line.strip() for line in log_file if line.strip()]

    recent = lines[-limit:]
    return [json.loads(line) for line in reversed(recent)]
