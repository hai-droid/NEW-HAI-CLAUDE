"""PreToolUse hook for Bash: the safety brakes that sit in front of every shell command.

Claude Code sends the pending tool call as JSON on stdin. We answer with a permission decision:
  deny – the command never runs; Claude gets the reason
  ask  – you get an approval prompt, even in auto-accept modes
  (no output) – normal permission flow
"""

import json
import re
import sys

try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)

cmd = (event.get("tool_input") or {}).get("command", "")
low = cmd.lower()


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


uses_meta_tool = "tools/meta.py" in low.replace("\\", "/")

# 1. Meta only through the official tool, which carries the brakes.
if re.search(r"graph\.facebook\.com|graph\.instagram\.com", low) and not uses_meta_tool:
    decide("deny", "גישה ישירה ל-Meta API חסומה. השתמש ב-tools/meta.py (PAUSED, תקרת תקציב, Dry Run).")

# 2. No deletes against the ad account, ever.
if re.search(r"-x\s*delete|method[\"']?\s*[:=]\s*[\"']?delete", low) and ("facebook" in low or uses_meta_tool):
    decide("deny", "מחיקה בחשבון הפרסום חסומה לחלוטין.")

# 3. Secrets stay out of the model's context.
creating_env = re.fullmatch(r"\s*(cp|copy)\s+\.env\.example\s+\.env\s*", cmd)
if re.search(r"(^|[\s/\\'\"=<])\.env($|[\s'\";|&>])", cmd) and not creating_env:
    decide("deny", "קובץ .env מכיל סודות ואסור לקרוא או להדפיס אותו. הכלים טוענים אותו לבד.")
if re.search(r"\b(echo|printenv|env|set)\b.*(meta_access_token|api_key|token)", low):
    decide("deny", "אסור להדפיס טוקנים ומפתחות.")

# 4. Anything that spends money or goes public needs a human yes.
if uses_meta_tool and "--execute" in low:
    decide("ask", "⚠️ פעולה אמיתית בחשבון Meta (נוצר הכל במצב PAUSED, בתוך תקרת התקציב). בדקת את ה-Dry Run? לאשר?")
if "landing.py" in low and " deploy" in low:
    decide("ask", "⚠️ העלאת דף נחיתה לאוויר (Vercel). לאשר?")
if re.search(r"\bvercel\b", low) and "landing.py" not in low:
    decide("ask", "פקודת Vercel ישירה. עדיף tools/landing.py deploy. לאשר בכל זאת?")

# 5. Protect client data and history.
if re.search(r"\brm\s+-[a-z]*r[a-z]*f?\b.*\bclients\b|remove-item.*clients.*-recurse|rmdir\s+/s.*clients", low):
    decide("deny", "מחיקת תיקיות לקוחות חסומה. אם באמת צריך – עשה את זה ידנית.")
if re.search(r"git\s+(push\s+.*(--force|-f\b)|reset\s+--hard|clean\s+-[a-z]*f)", low):
    decide("ask", "פקודת git שמוחקת היסטוריה או קבצים. לאשר?")

sys.exit(0)
