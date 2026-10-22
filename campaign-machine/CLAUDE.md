# Campaign Machine – an AI marketing department

This project is a marketing department of six agents that works on one client at a time. The user writes a request in Hebrew, the agents build, and the user reviews and approves.

## The team (`.claude/agents/`)
| Agent | Role | Writes |
|---|---|---|
| 👔 ceo | Reads the brief, sets strategy and angles, splits the work into tasks | `tasks.json` |
| ✍️ copywriter | Angles, hooks and ads in the client's voice | `copy.json` |
| 🎨 creative | On-brand ad images, 5 in parallel | `creatives.json`, `creatives/*.png` |
| 🖥️ landing | Landing page with a lead form and pixel, deploy | `landing/` |
| 🚀 campaigner | Meta campaign plan, dry run, creation in PAUSED status | `campaign-plan.json`, `meta-ids.json` |
| 📊 analyst | Reads results and turns conclusions into fix tasks | `report.md`, `fix-tasks.json` |

The main session is the office manager. It dispatches the agents according to the skills, passes context between them, and stops for human approval.

## Commands (`.claude/skills/`)
- `/new-client <slug> [url]`: new client folder + an interview that fills it in
- `/interview <client>`: a brief for a new campaign
- `/campaign <client> [what for]`: the full pipeline, from the brief to a campaign in PAUSED status
- `/analyze <client> [campaign]`: the analyst plus the fix loop
- `/office`: the agents office at http://localhost:3000/office
- `/checkpoint`: save or go back with git

## Structure
```
clients/<client>/
  business.md  brand-voice.md  config.json  assets/logo.png
  campaigns/<YYYY-MM-DD-slug>/
    brief.md tasks.json copy.json creatives.json creatives/ landing/
    campaign-plan.json meta-ids.json insights.json report.md fix-tasks.json
tools/      Python tools – the brakes are enforced here
templates/  landing page template
office/     the office event log
```

## Iron rules
1. **Separation between clients.** Work on one client at a time. Never read or copy another client's files into this client's work.
2. **Meta only through `tools/meta.py`.** Everything is created PAUSED. There is no activate or delete command. `--execute` only after the human has explicitly approved the dry run.
3. **Budget caps** are in `clients/<client>/config.json` → `safety`. Never edit them on your own. Only the user changes them.
4. **Secrets.** Never read, print or copy `.env`. The tools load it themselves.
5. **No making things up.** No invented prices, testimonials, numbers or interest IDs. Anything missing goes in as `TODO` or as a question to the user.
6. **Hebrew.** Talk to the user in Hebrew. Ads and pages are in Hebrew (unless the client asked otherwise), in the voice from `brand-voice.md`.
7. **Office reporting.** Every agent reports to the office at the start and at the end through `tools/log_event.py`.

## Running the tools
- Windows: `python tools/<tool>.py ...` · Mac/Linux: `python3 tools/<tool>.py ...`
- Always from the project root (where this file is).
- Campaign folder names are English, lowercase, digits and dashes only.
