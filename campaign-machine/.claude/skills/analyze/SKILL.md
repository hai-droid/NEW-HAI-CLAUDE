---
name: analyze
description: The fix loop. The analyst reads Meta results and writes conclusions and fix tasks, the CEO dispatches them, and the agents fix (with approval before every change in the account). Use when the user asks how a campaign is doing, or to optimize it.
argument-hint: <client-slug> [campaign-folder]
---

Run the analysis and fix loop: $ARGUMENTS

1. If no campaign was given, pick the most recent campaign of that client that has a `meta-ids.json`, and say which one.
2. Use the **analyst** subagent. It writes `report.md` and `fix-tasks.json`.
3. Show the user the bottom line and the list of findings → tasks, with the confidence of each.
4. Ask which tasks to run (the default is all of the high and medium ones). Use the **ceo** subagent to add them to `tasks.json`.
5. Run each approved task with its agent. Independent tasks (for example, new hooks plus creative variations) run in parallel.
   - Campaigner tasks (budget, pausing): dry run first, then `--execute` only after explicit approval.
   - New creatives or copy: these go into the campaign as new ads only through a new `campaign-plan.json` and another launch, after approval.
6. Finish with a summary: what was done, what is waiting for approval, and when to run the next analysis.
