#!/usr/bin/env python3
"""משיכת תוצאות הבחירות לכנסת ה-26 מאתר ועדת הבחירות ושמירתן כ-JSON.

הסקריפט משתמש רק בספרייה הסטנדרטית של פייתון (אין צורך ב-pip install).

שימוש:
    python3 fetcher.py              # משיכה אחת, כתיבה ל-data/results.json
    python3 fetcher.py --loop 60    # משיכה כל 60 שניות
    python3 fetcher.py --file page.html   # ניתוח קובץ ששמרתם ידנית מהאתר

הניתוח גמיש: הוא מחפש באתר טבלה (או JSON) שיש בה עמודת שם רשימה ועמודת
קולות, ומזהה עמודות לפי מילות מפתח בעברית. אם האתר לא מפרסם מנדטים, הם
מחושבים לפי שיטת באדר-עופר (אחוז חסימה 3.25% והסכמי עודפים מ-config.json).
"""

import argparse
import gzip
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_FILE = DATA_DIR / "results.json"
HISTORY_FILE = DATA_DIR / "history.json"
CONFIG_FILE = ROOT / "config.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# מילות מפתח לזיהוי עמודות. הסדר חשוב: בודקים קודם את הספציפיות.
COLUMN_HINTS = {
    "seats": ["מנדטים", "מנדט", "מושבים", "seats", "mandates"],
    "percent": ["אחוז", "%", "percent", "pct"],
    "votes": ["קולות", "מספר קולות", "כשרים", "votes"],
    "letters": ["אותיות", "אות", "סמל", "letters", "symbol"],
    "name": ["שם הרשימה", "רשימה", "מפלגה", "שם", "name", "party", "list"],
}

# תוויות לנתוני הסיכום הכלליים שמופיעים בדרך כלל בראש העמוד.
SUMMARY_LABELS = {
    "eligible": ["בעלי זכות בחירה", "בעלי זכות הצבעה", "בעלי זב\"ב"],
    "voters": ["מספר המצביעים", "מצביעים", "סה\"כ מצביעים"],
    "turnout": ["אחוז הצבעה", "אחוז ההצבעה"],
    "valid": ["קולות כשרים", "כשרים"],
    "invalid": ["קולות פסולים", "פסולים"],
    "ballots_counted": ["קלפיות שנספרו", "קלפיות שנקלטו", "נספרו"],
    "ballots_total": ["סה\"כ קלפיות", "מספר הקלפיות", "קלפיות"],
}


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- רשת

def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), resp.headers.get_content_type()


# ---------------------------------------------------------------- ניתוח HTML

class TableParser(HTMLParser):
    """אוסף את כל הטבלאות בעמוד, את הטקסט הגלוי ואת הקישורים."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []      # כל טבלה: רשימת שורות, כל שורה: רשימת תאים
        self._stack = []      # תמיכה בטבלאות מקוננות
        self._cell = None
        self.text = []
        self.links = []
        self.scripts = []
        self._in_script = False
        self._script_buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._stack.append([])
        elif tag == "tr" and self._stack:
            self._stack[-1].append([])
        elif tag in ("td", "th") and self._stack:
            self._cell = []
        elif tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        elif tag == "script":
            self._in_script = True
            self._script_buf = []
        elif tag in ("br", "p", "div", "li", "span"):
            self.text.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._stack:
            if not self._stack[-1]:
                self._stack[-1].append([])
            self._stack[-1][-1].append(clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "table" and self._stack:
            self.tables.append([r for r in self._stack.pop() if r])
        elif tag == "script":
            self._in_script = False
            self.scripts.append("".join(self._script_buf))

    def handle_data(self, data):
        if self._in_script:
            self._script_buf.append(data)
            return
        if self._cell is not None:
            self._cell.append(data)
        self.text.append(data)


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def to_number(s):
    """'1,234,567' / '3.25%' / '12' -> מספר. מחזיר None אם אין מספר."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return s
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(s))
    if not m:
        return None
    v = m.group(0).replace(",", "")
    return float(v) if "." in v else int(v)


def match_column(header):
    h = header.lower()
    for key, hints in COLUMN_HINTS.items():
        if any(hint.lower() in h for hint in hints):
            return key
    return None


def parse_party_table(table):
    """מזהה טבלת תוצאות לפי הכותרות ומחזיר רשימת מפלגות, או None."""
    if len(table) < 3:
        return None
    for header_idx in range(min(3, len(table))):
        header = table[header_idx]
        cols = {}
        for i, h in enumerate(header):
            key = match_column(h)
            if key and key not in cols:
                cols[key] = i
        if "votes" not in cols or "name" not in cols:
            continue
        parties = []
        for row in table[header_idx + 1:]:
            if len(row) <= max(cols.values()):
                continue
            name = row[cols["name"]]
            votes = to_number(row[cols["votes"]])
            if not name or votes is None or re.search(r"סה\"?כ|total", name, re.I):
                continue
            parties.append({
                "name": name,
                "letters": row[cols["letters"]] if "letters" in cols else "",
                "votes": int(votes),
                "percent": to_number(row[cols["percent"]]) if "percent" in cols else None,
                "seats": to_number(row[cols["seats"]]) if "seats" in cols else None,
            })
        if len(parties) >= 2:
            return parties
    return None


def parse_summary(text):
    """מחפש בטקסט הגלוי ערכים כמו 'אחוז הצבעה: 67.4%'."""
    summary = {}
    for key, labels in SUMMARY_LABELS.items():
        for label in labels:
            m = re.search(re.escape(label) + r"\s*[:\-]?\s*(\d[\d,]*(?:\.\d+)?)", text)
            if m:
                summary[key] = to_number(m.group(1))
                break
    return summary


# ---------------------------------------------------------------- ניתוח JSON

KEY_HINTS = {
    "name": ["name", "listname", "partyname", "shem", "title", "שם"],
    "letters": ["letters", "otiot", "symbol", "code", "אותיות"],
    "votes": ["votes", "kolot", "validvotes", "count", "קולות"],
    "percent": ["percent", "pct", "percentage", "achuz", "אחוז"],
    "seats": ["seats", "mandates", "mandats", "manda", "מנדטים"],
}


def _find_key(obj, hints):
    for k in obj:
        kl = k.lower().replace("_", "")
        if any(h in kl for h in hints):
            return k
    return None


def parse_json_results(data):
    """סורק JSON לעומק ומחפש מערך של אובייקטים עם שם וקולות."""
    best = None

    def walk(node):
        nonlocal best
        if isinstance(node, list) and len(node) >= 2 and all(isinstance(x, dict) for x in node):
            sample = node[0]
            nk = _find_key(sample, KEY_HINTS["name"])
            vk = _find_key(sample, KEY_HINTS["votes"])
            if nk and vk:
                lk = _find_key(sample, KEY_HINTS["letters"])
                pk = _find_key(sample, KEY_HINTS["percent"])
                sk = _find_key(sample, KEY_HINTS["seats"])
                parties = []
                for x in node:
                    v = to_number(x.get(vk))
                    if v is None or not x.get(nk):
                        continue
                    parties.append({
                        "name": clean(str(x.get(nk))),
                        "letters": clean(str(x.get(lk, ""))) if lk else "",
                        "votes": int(v),
                        "percent": to_number(x.get(pk)) if pk else None,
                        "seats": to_number(x.get(sk)) if sk else None,
                    })
                if len(parties) >= 2 and (best is None or len(parties) > len(best)):
                    best = parties
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return best


def json_from_scripts(scripts):
    """מחלץ אובייקטי JSON שמוטמעים בתגיות script (למשל __NEXT_DATA__)."""
    for s in scripts:
        s = s.strip()
        if not s:
            continue
        candidates = [s]
        candidates += re.findall(r"=\s*(\{.*\}|\[.*\])\s*;?\s*$", s, re.S)
        for c in candidates:
            try:
                yield json.loads(c)
            except (ValueError, TypeError):
                continue


# ---------------------------------------------------------------- איסוף

def scrape(config, html_file=None):
    """מחזיר (parties, summary, source_url). זורק RuntimeError אם לא נמצא כלום."""
    pages = []
    if html_file:
        pages.append((Path(html_file).read_text(encoding="utf-8", errors="replace"),
                      "text/html", str(html_file)))
    else:
        base = config["source"]["base_url"]
        urls = [urljoin(base, p) for p in config["source"]["paths"]]
        visited = set()
        errors = []
        while urls:
            url = urls.pop(0)
            if url in visited or len(visited) >= config["source"].get("max_pages", 8):
                continue
            visited.add(url)
            try:
                body, ctype = http_get(url)
            except Exception as e:  # noqa: BLE001 - רוצים להמשיך לעמוד הבא
                errors.append(f"{url}: {e}")
                continue
            pages.append((body, ctype, url))
            # עמוד ראשי בלי טבלה? ננסה קישורים שנראים כמו עמוד תוצאות ארציות.
            if "html" in ctype:
                p = TableParser()
                p.feed(body)
                for href in p.links:
                    if re.search(config["source"]["follow_links_regex"], href, re.I):
                        urls.append(urljoin(url, href))
        if not pages:
            raise RuntimeError("לא הצלחתי לטעון אף עמוד:\n" + "\n".join(errors))

    summary = {}
    for body, ctype, url in pages:
        parties = None
        if "json" in ctype or body.lstrip()[:1] in "[{":
            try:
                parties = parse_json_results(json.loads(body))
            except ValueError:
                parties = None
        if not parties:
            p = TableParser()
            p.feed(body)
            summary.update({k: v for k, v in parse_summary(clean(" ".join(p.text))).items()
                            if k not in summary})
            for t in p.tables:
                parties = parse_party_table(t)
                if parties:
                    break
            if not parties:
                for obj in json_from_scripts(p.scripts):
                    parties = parse_json_results(obj)
                    if parties:
                        break
        if parties:
            return parties, summary, url
    raise RuntimeError("העמודים נטענו אבל לא נמצאה בהם טבלת תוצאות. "
                       "עדכנו את source.paths ב-config.json לכתובת עמוד התוצאות הארציות.")


# ---------------------------------------------------------------- חישוב מנדטים

def dhondt(votes_by_key, seats):
    alloc = {k: 0 for k in votes_by_key}
    for _ in range(seats):
        k = max(votes_by_key, key=lambda x: (votes_by_key[x] / (alloc[x] + 1), votes_by_key[x]))
        alloc[k] += 1
    return alloc


def bader_ofer(parties, total_seats, threshold_pct, agreements, valid=None):
    """חלוקת מנדטים לפי חוק הבחירות: אחוז חסימה, באדר-עופר והסכמי עודפים.

    באדר-עופר שקולה לשיטת ד'הונט. הסכם עודפים מטופל כגוש אחד בחלוקה,
    ואחר כך המנדטים של הגוש מתחלקים בין שתי הרשימות שוב בד'הונט.
    """
    valid = valid or sum(p["votes"] for p in parties)
    if valid == 0:
        return {}
    threshold = valid * threshold_pct / 100
    passed = {p["name"]: p["votes"] for p in parties if p["votes"] >= threshold}
    if not passed:
        return {}

    def find(token):
        token = token.strip()
        for p in parties:
            if p["name"] in passed and (p["letters"] == token or token in p["name"]):
                return p["name"]
        return None

    bloc_of = {name: name for name in passed}
    for a, b in agreements:
        na, nb = find(a), find(b)
        if na and nb and na != nb and bloc_of[na] == na and bloc_of[nb] == nb:
            bloc_of[nb] = na
    blocs = {}
    for name, bloc in bloc_of.items():
        blocs.setdefault(bloc, []).append(name)
    bloc_votes = {b: sum(passed[n] for n in members) for b, members in blocs.items()}
    bloc_seats = dhondt(bloc_votes, total_seats)

    result = {}
    for b, members in blocs.items():
        if len(members) == 1:
            result[members[0]] = bloc_seats[b]
        else:
            result.update(dhondt({n: passed[n] for n in members}, bloc_seats[b]))
    return result


# ---------------------------------------------------------------- בניית הפלט

def build_snapshot(parties, summary, source_url, config):
    el = config["election"]
    # סך הקולות הכשרים מהאתר עדיף על סכימת הטבלה, שעשויה להשמיט רשימות קטנות.
    valid = max(summary.get("valid") or 0, sum(p["votes"] for p in parties))
    threshold_votes = valid * el["threshold_percent"] / 100
    official_seats = any(p.get("seats") for p in parties)
    computed = bader_ofer(parties, el["total_seats"], el["threshold_percent"],
                          config.get("surplus_agreements", []), valid)

    out_parties = []
    for p in parties:
        pct = p["percent"] if p.get("percent") is not None else (100 * p["votes"] / valid if valid else 0)
        seats = int(p["seats"] or 0) if official_seats else computed.get(p["name"], 0)
        out_parties.append({
            "name": p["name"],
            "letters": p.get("letters", ""),
            "votes": p["votes"],
            "percent": round(pct, 2),
            "seats": seats,
            "computed_seats": computed.get(p["name"], 0),
            "passed_threshold": p["votes"] >= threshold_votes,
        })
    out_parties.sort(key=lambda x: (-x["seats"], -x["votes"]))

    summary = dict(summary)
    summary.setdefault("valid", valid)
    if "turnout" not in summary and summary.get("eligible") and summary.get("voters"):
        summary["turnout"] = round(100 * summary["voters"] / summary["eligible"], 2)
    if summary.get("ballots_counted") and summary.get("ballots_total"):
        summary["counted_percent"] = round(100 * summary["ballots_counted"] / summary["ballots_total"], 1)

    return {
        "election": el["name"],
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source_url,
        "seats_source": "official" if official_seats else "computed",
        "total_seats": el["total_seats"],
        "majority": el["total_seats"] // 2 + 1,
        "threshold_percent": el["threshold_percent"],
        "threshold_votes": round(threshold_votes),
        "summary": summary,
        "parties": out_parties,
    }


def save(snapshot, history_limit):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = RESULTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(RESULTS_FILE)

    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except ValueError:
            history = []
    point = {
        "t": snapshot["updated_at"],
        "valid": snapshot["summary"].get("valid"),
        "seats": {p["name"]: p["seats"] for p in snapshot["parties"]},
        "percent": {p["name"]: p["percent"] for p in snapshot["parties"]},
    }
    # שומרים נקודה חדשה רק אם משהו השתנה, כדי שההיסטוריה תשקף עדכוני ספירה.
    if not history or history[-1]["valid"] != point["valid"] or history[-1]["seats"] != point["seats"]:
        history.append(point)
    history = history[-history_limit:]
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- main

def run_once(args, config):
    parties, summary, source = scrape(config, args.file)
    snap = build_snapshot(parties, summary, source, config)
    save(snap, config.get("history_limit", 500))
    seated = [p for p in snap["parties"] if p["seats"]]
    print(f"[{snap['updated_at']}] {len(snap['parties'])} רשימות, "
          f"{len(seated)} עברו, {snap['summary'].get('valid'):,} קולות כשרים, מקור: {source}")
    return snap


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--loop", type=int, metavar="SEC", help="למשוך שוב כל SEC שניות")
    ap.add_argument("--file", help="לנתח קובץ HTML/JSON מקומי במקום לגשת לאתר")
    args = ap.parse_args()
    config = load_config()

    if not args.loop:
        try:
            run_once(args, config)
        except Exception as e:  # noqa: BLE001
            print(f"שגיאה: {e}", file=sys.stderr)
            sys.exit(1)
        return
    while True:
        try:
            run_once(args, config)
        except Exception as e:  # noqa: BLE001 - בלולאה ממשיכים גם אחרי כשל
            print(f"שגיאה: {e}", file=sys.stderr)
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
