"""Report an agent's status to the agents office.

    python tools/log_event.py --agent copywriter --status working --msg "כותבת 5 הוקים" --client demo-studio
"""

import argparse

from common import log_event

AGENTS = ["ceo", "copywriter", "creative", "campaigner", "landing", "analyst", "human"]
STATUSES = ["queued", "working", "done", "waiting", "error", "idle"]

p = argparse.ArgumentParser()
p.add_argument("--agent", required=True, choices=AGENTS)
p.add_argument("--status", required=True, choices=STATUSES)
p.add_argument("--msg", required=True)
p.add_argument("--client")
p.add_argument("--campaign")
a = p.parse_args()
log_event(a.agent, a.status, a.msg, a.client, a.campaign)
print("ok")
