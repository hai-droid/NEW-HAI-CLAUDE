"""Landing pages for the landing agent.

    python tools/landing.py new      --client C --campaign DIR   # copy the template to landing/index.html
    python tools/landing.py finalize --client C --campaign DIR   # inject pixel + webhook, validate, build site folder
    python tools/landing.py preview  --client C --campaign DIR   # http://localhost:4000
    python tools/landing.py deploy   --client C --campaign DIR   # Vercel (asks for approval)
"""

import argparse
import functools
import http.server
import re
import shutil
import subprocess

from common import ROOT, campaign_dir, die, load_config, load_env, log_event, write_json

TEMPLATE = ROOT / "templates" / "landing.html"


def site_dir(client, camp):
    slug = re.sub(r"[^a-z0-9-]+", "-", f"{client}-{camp.name}".lower()).strip("-")[:90]
    return camp / "landing" / slug


def cmd_new(a):
    camp = campaign_dir(a.client, a.campaign)
    dst = camp / "landing" / "index.html"
    if dst.exists():
        die(f"{dst.relative_to(ROOT)} כבר קיים – ערוך אותו במקום ליצור חדש.")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATE, dst)
    print(f"✓ {dst.relative_to(ROOT)} – מלא את כל ה-[[...]]")


def cmd_finalize(a):
    cfg = load_config(a.client)
    camp = campaign_dir(a.client, a.campaign)
    src = camp / "landing" / "index.html"
    if not src.exists():
        die("אין landing/index.html. התחל עם: landing.py new")
    html = src.read_text(encoding="utf-8")
    colors = (cfg.get("brand", {}).get("colors") or []) + ["#1E1B4B", "#7C3AED", "#FACC15"]
    values = {
        "PIXEL_ID": cfg.get("meta", {}).get("pixel_id", ""),
        "LEAD_WEBHOOK": cfg.get("landing", {}).get("lead_webhook_url", ""),
        "CLIENT": a.client,
        "CAMPAIGN": camp.name,
        "COLOR_DARK": colors[0],
        "COLOR_MAIN": colors[1],
        "COLOR_ACCENT": colors[2],
    }
    for k, v in values.items():
        html = html.replace("{{" + k + "}}", v)

    errors, warnings = [], []
    left = sorted(set(re.findall(r"\[\[[^\]]*\]\]", html)))
    if left:
        errors.append(f"נשארו {len(left)} מקומות לא ממולאים: {', '.join(left[:5])}")
    if re.search(r"\{\{[A-Z_]+\}\}", html):
        errors.append("נשארו placeholders מסוג {{...}}.")
    if 'id="lead-form"' not in html:
        errors.append("חסר טופס לידים (id=lead-form).")
    if 'dir="rtl"' not in html:
        errors.append('חסר dir="rtl".')
    if not values["PIXEL_ID"]:
        warnings.append("אין meta.pixel_id – לא יימדדו לידים ב-Meta.")
    if not values["LEAD_WEBHOOK"]:
        warnings.append("אין landing.lead_webhook_url – הלידים לא יישמרו לשום מקום!")
    if errors:
        die("הדף לא עבר בדיקה:\n  - " + "\n  - ".join(errors))

    out = site_dir(a.client, camp)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    assets = camp / "landing" / "assets"
    if assets.is_dir():
        shutil.copytree(assets, out / "assets")
    for w in warnings:
        print(f"⚠️  {w}")
    print(f"✓ האתר מוכן: {out.relative_to(ROOT)}")
    log_event("landing", "done", "דף הנחיתה עבר בדיקה ומוכן לעלייה", a.client, camp.name)


def cmd_preview(a):
    camp = campaign_dir(a.client, a.campaign)
    out = site_dir(a.client, camp)
    if not out.exists():
        die("הרץ קודם finalize.")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    print(f"תצוגה מקדימה: http://localhost:{a.port}  (Ctrl+C לעצירה)")
    http.server.ThreadingHTTPServer(("127.0.0.1", a.port), handler).serve_forever()


def cmd_deploy(a):
    camp = campaign_dir(a.client, a.campaign)
    out = site_dir(a.client, camp)
    if not (out / "index.html").exists():
        die("הרץ קודם finalize.")
    npx = shutil.which("npx")
    if not npx:
        die("לא נמצא npx. התקן Node.js (ראה README).")
    log_event("landing", "working", "מעלה את הדף ל-Vercel", a.client, camp.name)
    res = subprocess.run([npx, "--yes", "vercel", "deploy", str(out), "--prod", "--yes"],
                         capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        die("ההעלאה נכשלה. אם זו הפעם הראשונה, הרץ פעם אחת בטרמינל: npx vercel login")
    urls = re.findall(r"https://[^\s]+\.vercel\.app", res.stdout + res.stderr)
    url = urls[-1] if urls else ""
    meta = camp / "landing" / "deploy.json"
    write_json(meta, {"url": url, "dir": str(out.relative_to(ROOT))})
    print(f"✅ הדף באוויר: {url}")
    log_event("landing", "done", f"הדף באוויר: {url}", a.client, camp.name)


def main():
    load_env()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("new", "finalize", "preview", "deploy"):
        sp = sub.add_parser(name)
        sp.add_argument("--client", required=True)
        sp.add_argument("--campaign", required=True)
        if name == "preview":
            sp.add_argument("--port", type=int, default=4000)
    a = p.parse_args()
    {"new": cmd_new, "finalize": cmd_finalize, "preview": cmd_preview, "deploy": cmd_deploy}[a.cmd](a)


if __name__ == "__main__":
    main()
