"""Meta (Facebook/Instagram) Marketing API tool for the campaigner and the analyst.

Safety brakes live here, in code, so no agent can talk its way past them:
  1. Everything is created PAUSED. This tool has no "activate" command at all.
  2. Hard budget caps from clients/<client>/config.json (daily and total).
  3. Dry run by default. Nothing is sent to Meta without --execute.
  4. --execute triggers an explicit approval prompt (tools/guard.py + settings.json).
  5. No delete. The tool never sends a DELETE request.
  6. Every write is logged to clients/<client>/meta-log.jsonl.

Commands:
  python tools/meta.py check     --client C
  python tools/meta.py interests --client C --q "יוגה"
  python tools/meta.py launch    --client C --campaign DIR [--execute]
  python tools/meta.py insights  --client C --campaign DIR [--days 7]
  python tools/meta.py budget    --client C --campaign DIR --adset KEY --daily 80 [--execute]
  python tools/meta.py pause     --client C --campaign DIR --id OBJECT_ID [--execute]
"""

import argparse
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from common import ROOT, campaign_dir, client_dir, die, load_config, load_env, log_event, now, read_json, write_json

API = "https://graph.facebook.com"
PAUSED = "PAUSED"


# ---------- HTTP ----------

def graph(method, path, params=None):
    assert method in ("GET", "POST"), "DELETE is blocked by design"
    version = os.environ.get("META_API_VERSION", "v24.0")
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        die("חסר META_ACCESS_TOKEN בקובץ .env (ראה README → חיבור Meta).")
    params = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
              for k, v in (params or {}).items()}
    params["access_token"] = token
    url = f"{API}/{version}/{path.lstrip('/')}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)["error"]
            msg = err.get("error_user_msg") or err.get("message")
            die(f"Meta החזירה שגיאה ({e.code}): {msg}")
        except (ValueError, KeyError):
            die(f"Meta החזירה שגיאה ({e.code}): {body[:500]}")
    except urllib.error.URLError as e:
        die(f"אין חיבור ל-Meta: {e.reason}")


def act(cfg):
    acc = cfg.get("meta", {}).get("ad_account_id", "")
    if not acc:
        die("חסר meta.ad_account_id ב-config.json של הלקוח.")
    return acc if acc.startswith("act_") else f"act_{acc}"


def audit(client, action, payload, result=None):
    path = client_dir(client) / "meta-log.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now(), "action": action, "payload": payload, "result": result},
                           ensure_ascii=False) + "\n")


def minor_units(amount):
    # Meta expects budgets in the currency's minor unit (agorot / cents).
    return int(round(float(amount) * 100))


# ---------- validation ----------

def validate_plan(plan, cfg, camp, execute):
    safety = cfg.get("safety", {})
    max_daily = float(safety.get("max_daily_budget", 0))
    max_total = float(safety.get("max_total_budget", 0))
    if max_daily <= 0:
        die("לא הוגדרה תקרת תקציב (safety.max_daily_budget) ב-config.json. בלי תקרה לא עובדים.")

    problems = []
    sets = plan.get("ad_sets", [])
    keys = {s.get("key") for s in sets}
    if not sets:
        problems.append("אין ad_sets בתוכנית.")
    daily = sum(float(s.get("daily_budget", 0)) for s in sets)
    if daily > max_daily:
        problems.append(f"סך התקציב היומי {daily} חורג מהתקרה {max_daily}.")
    days = float(plan.get("duration_days", 0) or 0)
    if days <= 0:
        problems.append("חסר duration_days בתוכנית (כמה ימים הקמפיין ירוץ).")
    elif max_total and daily * days > max_total:
        problems.append(f"התקציב הכולל {daily * days:.0f} חורג מהתקרה הכוללת {max_total}.")
    for s in sets:
        if float(s.get("daily_budget", 0)) <= 0:
            problems.append(f"ad set {s.get('key')}: חסר daily_budget.")
    ads = plan.get("ads", [])
    if not ads:
        problems.append("אין ads בתוכנית.")
    for ad in ads:
        if ad.get("ad_set") not in keys:
            problems.append(f"מודעה {ad.get('key')}: ad_set לא קיים.")
        img = camp / ad.get("image", "")
        if not ad.get("image") or not img.is_file():
            problems.append(f"מודעה {ad.get('key')}: קובץ תמונה לא נמצא ({ad.get('image')}).")
        for field in ("primary_text", "headline", "link"):
            if not ad.get(field):
                problems.append(f"מודעה {ad.get('key')}: חסר {field}.")
    if not cfg.get("meta", {}).get("page_id"):
        if execute:
            problems.append("חסר meta.page_id ב-config.json.")
        else:
            print("⚠️  חסר meta.page_id ב-config.json – חובה לפני --execute.")
    if problems:
        die("התוכנית לא עברה בדיקה:\n  - " + "\n  - ".join(problems))
    return daily, days


# ---------- commands ----------

def cmd_check(a):
    cfg = load_config(a.client)
    me = graph("GET", "me", {"fields": "id,name"})
    acc = graph("GET", act(cfg), {"fields": "name,currency,account_status,amount_spent,spend_cap"})
    print(f"✓ מחובר כ: {me.get('name')} ({me.get('id')})")
    print(f"✓ חשבון מודעות: {acc.get('name')} · מטבע {acc.get('currency')} · סטטוס {acc.get('account_status')}")
    page = cfg.get("meta", {}).get("page_id")
    if page:
        p = graph("GET", page, {"fields": "name"})
        print(f"✓ עמוד: {p.get('name')}")
    if cfg.get("meta", {}).get("pixel_id"):
        px = graph("GET", cfg["meta"]["pixel_id"], {"fields": "name,last_fired_time"})
        print(f"✓ פיקסל: {px.get('name')} · נורה לאחרונה: {px.get('last_fired_time', 'אף פעם')}")
    cur = cfg.get("safety", {}).get("currency")
    if cur and acc.get("currency") and cur != acc.get("currency"):
        print(f"⚠️  המטבע ב-config ({cur}) שונה מהמטבע בחשבון ({acc.get('currency')}). תקן לפני השקה.")


def cmd_interests(a):
    res = graph("GET", "search", {"type": "adinterest", "q": a.q, "limit": 15, "locale": "he_IL"})
    for it in res.get("data", []):
        size = it.get("audience_size_upper_bound") or it.get("audience_size")
        print(f"{it['id']}\t{it['name']}\t{size}")


def build_adset_payload(s, cfg, campaign_id):
    targeting = dict(s.get("targeting") or {})
    targeting.setdefault("geo_locations", {"countries": ["IL"]})
    targeting.setdefault("targeting_automation", {"advantage_audience": 0})
    payload = {
        "name": s["name"],
        "campaign_id": campaign_id,
        "daily_budget": minor_units(s["daily_budget"]),
        "billing_event": "IMPRESSIONS",
        "optimization_goal": s.get("optimization_goal", "OFFSITE_CONVERSIONS"),
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "destination_type": s.get("destination_type", "WEBSITE"),
        "targeting": targeting,
        "status": PAUSED,
    }
    pixel = cfg.get("meta", {}).get("pixel_id")
    if payload["optimization_goal"] == "OFFSITE_CONVERSIONS":
        if not pixel:
            die("אופטימיזציה להמרות דורשת meta.pixel_id ב-config.json (או optimization_goal=LINK_CLICKS).")
        payload["promoted_object"] = {"pixel_id": pixel, "custom_event_type": s.get("event", "LEAD")}
    if s.get("start_time"):
        payload["start_time"] = s["start_time"]
    return payload


def build_creative_payload(ad, cfg, image_hash):
    meta = cfg["meta"]
    link_data = {
        "image_hash": image_hash,
        "link": ad["link"],
        "message": ad["primary_text"],
        "name": ad["headline"],
        "call_to_action": {"type": ad.get("cta", "LEARN_MORE"), "value": {"link": ad["link"]}},
    }
    if ad.get("description"):
        link_data["description"] = ad["description"]
    spec = {"page_id": meta["page_id"], "link_data": link_data}
    if meta.get("instagram_user_id"):
        spec["instagram_user_id"] = meta["instagram_user_id"]
    return {"name": f"{ad['key']} · creative", "object_story_spec": spec}


def cmd_launch(a):
    cfg = load_config(a.client)
    camp = campaign_dir(a.client, a.campaign)
    plan_path = camp / "campaign-plan.json"
    if not plan_path.exists():
        die(f"לא נמצא {plan_path.relative_to(ROOT)}")
    plan = read_json(plan_path)
    daily, days = validate_plan(plan, cfg, camp, a.execute)
    cur = cfg.get("safety", {}).get("currency", "")
    c = plan["campaign"]

    print("=" * 60)
    print(f"{'DRY RUN – שום דבר לא נשלח ל-Meta' if not a.execute else 'EXECUTE – יוצר ב-Meta (הכל PAUSED)'}")
    print("=" * 60)
    print(f"קמפיין: {c['name']} · מטרה {c.get('objective', 'OUTCOME_LEADS')} · סטטוס PAUSED")
    print(f"תקציב יומי כולל: {daily:g} {cur} (תקרה {cfg['safety']['max_daily_budget']}) · "
          f"{days:g} ימים ≈ {daily * days:,.0f} {cur}")
    for s in plan["ad_sets"]:
        t = s.get("targeting", {})
        print(f"  • ad set {s['key']}: {s['name']} · {s['daily_budget']} {cur}/יום · "
              f"גילאים {t.get('age_min', 18)}-{t.get('age_max', 65)}")
        for ad in [x for x in plan["ads"] if x["ad_set"] == s["key"]]:
            print(f"      – מודעה {ad['key']}: \"{ad['headline']}\" · {ad['image']} → {ad['link']}")
    if not a.execute:
        print("\nכדי ליצור בפועל (במצב PAUSED): הוסף --execute. תתבקש לאשר.")
        log_event("campaigner", "waiting", "Dry Run מוכן – ממתין לאישור אנושי", a.client, camp.name)
        return

    account = act(cfg)
    ids = {"campaign": None, "ad_sets": {}, "ads": {}, "creatives": {}, "images": {}}
    payload = {
        "name": c["name"],
        "objective": c.get("objective", "OUTCOME_LEADS"),
        "special_ad_categories": c.get("special_ad_categories", []),
        "is_adset_budget_sharing_enabled": False,
        "status": PAUSED,
    }
    res = graph("POST", f"{account}/campaigns", payload)
    audit(a.client, "create_campaign", payload, res)
    ids["campaign"] = res["id"]
    print(f"✓ קמפיין נוצר: {res['id']} (PAUSED)")

    for s in plan["ad_sets"]:
        p = build_adset_payload(s, cfg, ids["campaign"])
        r = graph("POST", f"{account}/adsets", p)
        audit(a.client, "create_adset", p, r)
        ids["ad_sets"][s["key"]] = r["id"]
        print(f"✓ ad set {s['key']}: {r['id']} (PAUSED)")

    for ad in plan["ads"]:
        img = camp / ad["image"]
        if ad["image"] not in ids["images"]:
            r = graph("POST", f"{account}/adimages",
                      {"bytes": base64.b64encode(img.read_bytes()).decode()})
            ids["images"][ad["image"]] = next(iter(r["images"].values()))["hash"]
        cp = build_creative_payload(ad, cfg, ids["images"][ad["image"]])
        r = graph("POST", f"{account}/adcreatives", cp)
        audit(a.client, "create_creative", cp, r)
        ids["creatives"][ad["key"]] = r["id"]
        ap = {"name": ad.get("name", ad["key"]), "adset_id": ids["ad_sets"][ad["ad_set"]],
              "creative": {"creative_id": r["id"]}, "status": PAUSED}
        r = graph("POST", f"{account}/ads", ap)
        audit(a.client, "create_ad", ap, r)
        ids["ads"][ad["key"]] = r["id"]
        print(f"✓ מודעה {ad['key']}: {r['id']} (PAUSED)")

    write_json(camp / "meta-ids.json", ids)
    log_event("campaigner", "done", f"הקמפיין נוצר ב-Meta במצב PAUSED ({ids['campaign']})", a.client, camp.name)
    print("\n✅ הכל נוצר במצב PAUSED. בדוק ב-Ads Manager והפעל ידנית כשאתה מוכן.")


def cmd_insights(a):
    camp = campaign_dir(a.client, a.campaign)
    ids_path = camp / "meta-ids.json"
    if not ids_path.exists():
        die("אין meta-ids.json – הקמפיין עוד לא נוצר ב-Meta.")
    ids = read_json(ids_path)
    fields = ("ad_id,ad_name,adset_id,adset_name,spend,impressions,reach,frequency,clicks,"
              "inline_link_clicks,ctr,cpc,cpm,actions,cost_per_action_type")
    rows = []
    res = graph("GET", f"{ids['campaign']}/insights",
                {"level": "ad", "fields": fields, "date_preset": f"last_{a.days}d"
                 if a.days in (3, 7, 14, 28, 30, 90) else "maximum", "limit": 500})
    rows.extend(res.get("data", []))
    for r in rows:
        acts = {x["action_type"]: float(x["value"]) for x in r.get("actions", [])}
        r["leads"] = acts.get("lead", 0) + acts.get("offsite_conversion.fb_pixel_lead", 0)
        r["cpl"] = round(float(r.get("spend", 0)) / r["leads"], 2) if r["leads"] else None
    out = {"fetched_at": now(), "days": a.days, "rows": rows}
    write_json(camp / "insights.json", out)
    print(f"✓ נשמרו {len(rows)} שורות ל-{(camp / 'insights.json').relative_to(ROOT)}")
    for r in rows:
        print(f"  {r.get('ad_name')}: הוצאה {r.get('spend')} · CTR {r.get('ctr')} · לידים {r['leads']:g} · CPL {r['cpl']}")


def cmd_budget(a):
    cfg = load_config(a.client)
    camp = campaign_dir(a.client, a.campaign)
    ids = read_json(camp / "meta-ids.json")
    plan = read_json(camp / "campaign-plan.json")
    if a.adset not in ids["ad_sets"]:
        die(f"ad set {a.adset} לא קיים. קיימים: {', '.join(ids['ad_sets'])}")
    others = sum(float(s["daily_budget"]) for s in plan["ad_sets"] if s["key"] != a.adset)
    cap = float(cfg["safety"]["max_daily_budget"])
    if others + a.daily > cap:
        die(f"השינוי יביא את התקציב היומי ל-{others + a.daily:g}, מעל התקרה {cap:g}. נחסם.")
    print(f"ad set {a.adset}: תקציב יומי חדש {a.daily:g} · סה\"כ יומי {others + a.daily:g}/{cap:g}")
    if not a.execute:
        print("DRY RUN. הוסף --execute כדי לעדכן.")
        return
    p = {"daily_budget": minor_units(a.daily)}
    r = graph("POST", ids["ad_sets"][a.adset], p)
    audit(a.client, "update_budget", {"adset": a.adset, **p}, r)
    for s in plan["ad_sets"]:
        if s["key"] == a.adset:
            s["daily_budget"] = a.daily
    write_json(camp / "campaign-plan.json", plan)
    print("✓ עודכן")


def cmd_pause(a):
    camp = campaign_dir(a.client, a.campaign)
    ids = read_json(camp / "meta-ids.json")
    known = {ids["campaign"], *ids["ad_sets"].values(), *ids["ads"].values()}
    if a.id not in known:
        die("אפשר לעצור רק אובייקטים שנוצרו בקמפיין הזה.")
    print(f"עצירת {a.id} (PAUSED)")
    if not a.execute:
        print("DRY RUN. הוסף --execute כדי לעצור.")
        return
    r = graph("POST", a.id, {"status": PAUSED})
    audit(a.client, "pause", {"id": a.id}, r)
    print("✓ נעצר")


def main():
    load_env()
    p = argparse.ArgumentParser(description="Meta Marketing API – עם בלמי בטיחות")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "interests", "launch", "insights", "budget", "pause"):
        sp = sub.add_parser(name)
        sp.add_argument("--client", required=True)
        if name != "check" and name != "interests":
            sp.add_argument("--campaign", required=True)
        if name in ("launch", "budget", "pause"):
            sp.add_argument("--execute", action="store_true")
        if name == "interests":
            sp.add_argument("--q", required=True)
        if name == "insights":
            sp.add_argument("--days", type=int, default=7)
        if name == "budget":
            sp.add_argument("--adset", required=True)
            sp.add_argument("--daily", type=float, required=True)
        if name == "pause":
            sp.add_argument("--id", required=True)
    a = p.parse_args()
    {"check": cmd_check, "interests": cmd_interests, "launch": cmd_launch,
     "insights": cmd_insights, "budget": cmd_budget, "pause": cmd_pause}[a.cmd](a)


if __name__ == "__main__":
    main()
