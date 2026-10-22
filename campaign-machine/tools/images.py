"""Ad creatives for the creative agent.

AI models are good at backgrounds and bad at Hebrew lettering, so every creative is built in two steps:
  1. generate: an AI image API makes a background with no text (OpenAI or Gemini, from .env)
  2. compose:  Pillow lays the Hebrew headline, sub-line, CTA button and logo on top, in brand colors

    python tools/images.py batch --client C --campaign DIR     # all of creatives.json, in parallel
    python tools/images.py compose --client C --bg bg.png --headline "..." --out out.png

creatives.json (written by the creative agent inside the campaign folder):
  {"creatives": [{"id": "c1", "format": "feed", "bg_prompt": "...", "headline": "...",
                  "sub": "...", "cta": "...", "layout": "bottom"}]}
"""

import argparse
import base64
import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import ROOT, campaign_dir, client_dir, die, load_config, load_env, log_event, read_json, write_json

try:
    from PIL import Image, ImageDraw, ImageFont, features
except ImportError:
    die("חסרה הספרייה Pillow. הרץ: pip install -r requirements.txt")

FORMATS = {"feed": (1080, 1350), "square": (1080, 1080), "story": (1080, 1920)}
FONT_CANDIDATES = [
    ROOT / "fonts" / "Heebo-Bold.ttf",
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    Path("/Library/Fonts/Arial Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
RAQM = features.check("raqm")


# ---------- AI backgrounds ----------

def _post_json(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Image API error {e.code}: {e.read().decode(errors='replace')[:400]}")


def generate_background(prompt, fmt, out):
    provider = os.environ.get("IMAGE_PROVIDER", "none").lower()
    prompt = (f"{prompt}. Advertising photo background. Absolutely no text, letters, logos or "
              f"watermarks. Leave calm empty space in the lower third for a headline.")
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY") or die("חסר OPENAI_API_KEY ב-.env")
        size = {"feed": "1024x1536", "story": "1024x1536", "square": "1024x1024"}[fmt]
        res = _post_json("https://api.openai.com/v1/images/generations",
                         {"model": os.environ.get("IMAGE_MODEL", "gpt-image-1"), "prompt": prompt,
                          "size": size, "n": 1},
                         {"Authorization": f"Bearer {key}"})
        data = base64.b64decode(res["data"][0]["b64_json"])
    elif provider == "gemini":
        key = os.environ.get("GEMINI_API_KEY") or die("חסר GEMINI_API_KEY ב-.env")
        model = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")
        ratio = {"feed": "4:5", "story": "9:16", "square": "1:1"}[fmt]
        res = _post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                         {"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"responseModalities": ["IMAGE"],
                                               "imageConfig": {"aspectRatio": ratio}}},
                         {"x-goog-api-key": key})
        parts = res["candidates"][0]["content"]["parts"]
        data = base64.b64decode(next(p["inlineData"]["data"] for p in parts if "inlineData" in p))
    else:
        return None  # no provider: compose() falls back to a brand-color gradient
    Path(out).write_bytes(data)
    return out


# ---------- composition ----------

def font(cfg, size):
    custom = cfg.get("brand", {}).get("font")
    for path in ([ROOT / custom] if custom else []) + FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(str(path), size)
    die("לא נמצא פונט עם תמיכה בעברית. שים קובץ Heebo-Bold.ttf בתיקייה fonts/.")


def shape(text):
    """Return text ready to draw right-to-left, with or without libraqm."""
    if RAQM:
        return text, {"direction": "rtl", "language": "he"}
    try:
        from bidi.algorithm import get_display
    except ImportError:
        from bidi import get_display  # python-bidi >= 0.5
    return get_display(text), {}


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        t, kw = shape(test)
        if draw.textlength(t, font=fnt, **kw) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover(img, size):
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale + 1), int(img.height * scale + 1)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def gradient(size, c1, c2):
    w, h = size
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)
    mask = Image.linear_gradient("L").resize(size)
    return Image.composite(top, base, mask)


def compose(cfg, bg_path, headline, sub, cta, out, fmt="feed", layout="bottom", client_path=None):
    size = FORMATS[fmt]
    W, H = size
    colors = cfg.get("brand", {}).get("colors") or ["#1E1B4B", "#7C3AED", "#FACC15"]
    c_dark, c_main = hex_rgb(colors[0]), hex_rgb(colors[1] if len(colors) > 1 else colors[0])
    c_accent = hex_rgb(colors[2] if len(colors) > 2 else "#FFFFFF")

    if bg_path and Path(bg_path).is_file():
        img = cover(Image.open(bg_path).convert("RGB"), size)
    else:
        img = gradient(size, c_main, c_dark)

    # Darken the text zone so the copy reads on any background.
    shade = Image.new("L", size, 0)
    sd = ImageDraw.Draw(shade)
    zone = range(int(H * 0.45), H) if layout == "bottom" else range(0, int(H * 0.55))
    for y in zone:
        frac = (y - zone.start) / max(1, len(zone))
        alpha = int(210 * (frac if layout == "bottom" else 1 - frac))
        sd.line([(0, y), (W, y)], fill=alpha)
    img = Image.composite(Image.new("RGB", size, c_dark), img, shade)

    draw = ImageDraw.Draw(img)
    pad = 80
    head_size = 92 if fmt != "story" else 104
    head_lh = int(head_size * 1.2)
    f_head = font(cfg, head_size)
    f_sub = font(cfg, 46)
    f_cta = font(cfg, 44)

    head_lines = wrap(draw, headline, f_head, W - 2 * pad)
    sub_lines = wrap(draw, sub, f_sub, W - 2 * pad) if sub else []
    block_h = len(head_lines) * head_lh + len(sub_lines) * 62 + (130 if cta else 0)
    y = H - pad - block_h - (120 if fmt == "story" else 0) if layout == "bottom" else pad + 140

    for line in head_lines:
        t, kw = shape(line)
        draw.text((W - pad, y), t, font=f_head, fill="white", anchor="ra", **kw)
        y += head_lh
    y += 20
    for line in sub_lines:
        t, kw = shape(line)
        draw.text((W - pad, y), t, font=f_sub, fill=(235, 235, 245), anchor="ra", **kw)
        y += 62
    if cta:
        y += 30
        t, kw = shape(cta)
        tw = draw.textlength(t, font=f_cta, **kw)
        box = (W - pad - tw - 80, y, W - pad, y + 96)
        draw.rounded_rectangle(box, radius=48, fill=c_accent)
        text_fill = "black" if sum(c_accent) > 380 else "white"
        draw.text(((box[0] + box[2]) / 2, y + 48), t, font=f_cta, fill=text_fill, anchor="mm", **kw)

    logo = cfg.get("brand", {}).get("logo")
    if logo and client_path and (client_path / logo).is_file():
        lg = Image.open(client_path / logo).convert("RGBA")
        lg.thumbnail((220, 120))
        img.paste(lg, (pad, pad), lg)

    img.save(out, quality=92)
    return out


# ---------- commands ----------

def make_one(cfg, client, camp, c):
    out_dir = camp / "creatives"
    out_dir.mkdir(exist_ok=True)
    fmt = c.get("format", "feed")
    bg = out_dir / f"{c['id']}-bg.png"
    try:
        if not bg.exists():
            generate_background(c.get("bg_prompt", ""), fmt, bg)
    except Exception as e:  # keep going with a gradient; report it
        print(f"⚠️  {c['id']}: רקע AI נכשל ({e}). משתמש ברקע במיתוג.")
    out = out_dir / f"{c['id']}.png"
    compose(cfg, bg, c["headline"], c.get("sub", ""), c.get("cta", ""), out, fmt,
            c.get("layout", "bottom"), client_dir(client))
    return out


def cmd_batch(a):
    cfg = load_config(a.client)
    camp = campaign_dir(a.client, a.campaign)
    spec = read_json(camp / "creatives.json")["creatives"]
    log_event("creative", "working", f"מייצרת {len(spec)} קריאייטיבים במקביל", a.client, camp.name)
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda c: make_one(cfg, a.client, camp, c), spec))
    for r in results:
        print(f"✓ {r.relative_to(ROOT)}")
    log_event("creative", "done", f"{len(results)} קריאייטיבים מוכנים", a.client, camp.name)


def cmd_compose(a):
    cfg = load_config(a.client)
    out = compose(cfg, a.bg, a.headline, a.sub, a.cta, a.out, a.format, a.layout, client_dir(a.client))
    print(f"✓ {out}")


def main():
    load_env()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--client", required=True)
    b.add_argument("--campaign", required=True)
    c = sub.add_parser("compose")
    c.add_argument("--client", required=True)
    c.add_argument("--bg")
    c.add_argument("--headline", required=True)
    c.add_argument("--sub", default="")
    c.add_argument("--cta", default="")
    c.add_argument("--out", required=True)
    c.add_argument("--format", default="feed", choices=list(FORMATS))
    c.add_argument("--layout", default="bottom", choices=["bottom", "top"])
    a = p.parse_args()
    {"batch": cmd_batch, "compose": cmd_compose}[a.cmd](a)


if __name__ == "__main__":
    main()
