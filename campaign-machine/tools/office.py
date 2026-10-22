"""The agents office: a live control room at http://localhost:3000/office

    python tools/office.py            # Ctrl+C to stop

Reads office/events.jsonl (written by the agents and hooks) and the campaign folders, nothing else.
"""

import json
import mimetypes
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import CLIENTS, OFFICE_LOG, ROOT

PAGE = ROOT / "tools" / "office" / "index.html"
TEAM = ["ceo", "copywriter", "creative", "campaigner", "landing", "analyst"]
STEPS = [  # (file in campaign folder, label, agent)
    ("brief.md", "בריף", "ceo"),
    ("tasks.json", "משימות", "ceo"),
    ("copy.json", "קופי", "copywriter"),
    ("creatives", "קריאייטיב", "creative"),
    ("landing/index.html", "דף נחיתה", "landing"),
    ("campaign-plan.json", "תוכנית קמפיין", "campaigner"),
    ("meta-ids.json", "נוצר ב-Meta", "campaigner"),
    ("report.md", "ניתוח", "analyst"),
]


def events(limit=300):
    if not OFFICE_LOG.exists():
        return []
    lines = OFFICE_LOG.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def campaigns():
    out = []
    for camp in sorted(CLIENTS.glob("*/campaigns/*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not camp.is_dir() or camp.parent.parent.name.startswith("_"):
            continue
        steps = [{"label": label, "agent": agent, "done": (camp / f).exists()} for f, label, agent in STEPS]
        images = sorted(str(p.relative_to(ROOT)).replace("\\", "/")
                        for p in (camp / "creatives").glob("*.png") if not p.name.endswith("-bg.png"))
        deploy = camp / "landing" / "deploy.json"
        out.append({
            "client": camp.parent.parent.name,
            "campaign": camp.name,
            "steps": steps,
            "images": images[:10],
            "landing_url": json.loads(deploy.read_text(encoding="utf-8")).get("url") if deploy.exists() else None,
        })
    return out[:12]


def state():
    evs = events()
    agents = {a: {"status": "idle", "msg": "", "ts": ""} for a in TEAM}
    for e in evs:
        if e.get("agent") in agents:
            agents[e["agent"]] = {"status": e["status"], "msg": e["msg"], "ts": e["ts"]}
    return {"agents": agents, "events": evs[-60:][::-1], "campaigns": campaigns()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/office")
            self.end_headers()
        elif path == "/office":
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/state":
            self.send(200, json.dumps(state(), ensure_ascii=False).encode(), "application/json; charset=utf-8")
        elif path.startswith("/files/"):
            # Only images from inside clients/ – nothing else on disk is reachable.
            target = (ROOT / urllib.parse.unquote(path[len("/files/"):])).resolve()
            ok = CLIENTS.resolve() in target.parents and target.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            if ok and target.is_file():
                self.send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or "image/png")
            else:
                self.send(404, b"not found", "text/plain")
        else:
            self.send(404, b"not found", "text/plain")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"🏢 משרד הסוכנים פתוח: http://localhost:{port}/office  (Ctrl+C לסגירה)")
    try:
        ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
