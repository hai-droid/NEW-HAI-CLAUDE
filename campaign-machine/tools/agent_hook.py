"""SubagentStart / SubagentStop hook: lights agents up in the office automatically."""

import json
import sys

from common import log_event

TEAM = {"ceo", "copywriter", "creative", "campaigner", "landing", "analyst"}

try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)

agent = (event.get("agent_type") or "").split(":")[-1]
if agent in TEAM:
    if event.get("hook_event_name") == "SubagentStart":
        log_event(agent, "working", "התחיל לעבוד")
    elif event.get("hook_event_name") == "SubagentStop" and not event.get("stop_hook_active"):
        log_event(agent, "done", "סיים את המשימה")
sys.exit(0)
