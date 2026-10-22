"""Shared helpers for the campaign-machine tools: paths, .env, client config, office log."""

import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENTS = ROOT / "clients"
OFFICE_LOG = ROOT / "office" / "events.jsonl"

# Hebrew output on Windows consoles.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env():
    """Load KEY=VALUE lines from .env into os.environ (without overriding real env vars)."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def die(msg, code=1):
    print(f"✋ {msg}", file=sys.stderr)
    sys.exit(code)


def client_dir(client):
    if not client or "/" in client or "\\" in client or client.startswith((".", "_")):
        die(f"שם לקוח לא תקין: {client!r}")
    path = CLIENTS / client
    if not path.is_dir():
        die(f"לא נמצאה תיקיית לקוח: clients/{client}. צור אותה עם /new-client.")
    return path


def load_config(client):
    path = client_dir(client) / "config.json"
    if not path.exists():
        die(f"חסר clients/{client}/config.json")
    return json.loads(path.read_text(encoding="utf-8"))


def campaign_dir(client, campaign):
    """Resolve a campaign folder and make sure it stays inside the client's folder."""
    base = client_dir(client) / "campaigns"
    path = (base / campaign).resolve()
    if base.resolve() not in path.parents:
        die("נתיב קמפיין מחוץ לתיקיית הלקוח – נחסם (הפרדה בין לקוחות).")
    if not path.is_dir():
        die(f"לא נמצאה תיקיית קמפיין: {path.relative_to(ROOT)}")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def log_event(agent, status, msg, client=None, campaign=None):
    """Append an event to the agents-office feed (office/events.jsonl)."""
    OFFICE_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": now(), "agent": agent, "status": status, "msg": msg}
    if client:
        event["client"] = client
    if campaign:
        event["campaign"] = campaign
    with OFFICE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
