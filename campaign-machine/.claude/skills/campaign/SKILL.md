---
name: campaign
description: Run the whole marketing department end to end, from one brief to a Meta campaign ready in PAUSED status. CEO → copywriter → creative + landing in parallel → campaigner → human approval. Use when the user asks to build or launch a campaign.
argument-hint: <client-slug> [what the campaign is for]
---

Run the full campaign pipeline: $ARGUMENTS

You are the office manager. You don't do the agents' work. You dispatch them in order, pass context between them, and stop for the human at the approval points.

## 0. Preparation
- Start the office in the background if it isn't running: `python tools/office.py` (Mac: `python3`), and tell the user to open http://localhost:3000/office.
- Check that `clients/<client>/` exists. If not, run the `/new-client` flow first.
- If there is no campaign folder with a `brief.md` for this campaign, run the `/interview` flow first. The brief needs human approval.
- `python tools/log_event.py --agent human --status done --msg "בריף אושר" --client <client> --campaign <campaign>`

## 1. CEO
Use the **ceo** subagent: "Client <client>, campaign <campaign>. Read the brief and the client files, and write tasks.json." Show the user the big idea, the angles and the open questions. If there are open questions that block the work, ask them now.

## 2. Copywriter
Use the **copywriter** subagent with its task from tasks.json. Show the user the 5 hooks.

## 3. Creative + landing page, in parallel
Launch **creative** and **landing** together, in the same message, so they run at the same time. Each gets its task from tasks.json. When both are done:
- Show the creative file paths (the user can look at them in the office).
- Suggest a preview of the page: `python tools/landing.py preview --client <client> --campaign <campaign>`

## 4. 🧑 Human check
Ask the user to review the hooks, the creatives and the page, and to approve or ask for changes. Send changes back to the right agent. Then ask whether to upload the landing page (`landing.py deploy`, with its own approval prompt).

## 5. Campaigner
Use the **campaigner** subagent. It writes campaign-plan.json and runs a dry run. Show the user the dry-run output and a summary: budget per day and in total, audiences, and which ad goes where.

## 6. 🧑 Final approval
Only if the user explicitly approves (for example "מאשר", "תעלה"), run `python tools/meta.py launch --client <client> --campaign <campaign> --execute`. Claude Code will ask for one more approval. Without explicit approval, stop here and say that everything is ready.

## 7. Closing
- `python tools/log_event.py --agent human --status done --msg "הקמפיין מוכן ב-Meta (PAUSED)" --client <client> --campaign <campaign>`
- Commit a checkpoint: `git add clients/<client> && git commit -m "campaign: <client>/<campaign>"` (if this is a git repo).
- Tell the user that everything is PAUSED in Meta and has to be turned on manually in Ads Manager, and that in 3–7 days they should run `/analyze <client> <campaign>`.
