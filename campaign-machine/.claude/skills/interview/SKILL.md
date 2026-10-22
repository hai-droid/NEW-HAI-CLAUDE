---
name: interview
description: The briefing interview. Asks the user short questions and writes the campaign's brief.md. Use at the start of a new campaign when there is no brief yet.
argument-hint: <client-slug> [what the campaign is for]
---

Run a briefing interview for a new campaign: $ARGUMENTS

1. Make sure `clients/<client>/` exists (if not, suggest `/new-client`). Read `business.md`, `brand-voice.md`, `config.json` and earlier campaigns' `report.md` so you don't ask what is already known.
2. Create the campaign folder `clients/<client>/campaigns/<YYYY-MM-DD>-<short-english-slug>/` (lowercase, digits, dashes only).
3. Ask in Hebrew, in 2–3 short rounds. Skip anything already answered:
   - What are we promoting (a product, a service, a webinar, an event, an offer)? What's the offer, and until when?
   - Who is it for this time? The same audience as always, or a specific segment?
   - What counts as success: leads, sign-ups, sales? Is there a target cost per lead?
   - Budget: per day and number of days (remind them of the caps in `config.json`).
   - Where should people land: a new landing page (the default) or an existing page?
   - Anything else: dates, constraints, what definitely not to say.
4. Write `brief.md`: the goal, offer, audience, KPI, budget and dates, landing page, constraints, and open questions.
5. Show the brief and ask for approval or corrections. Don't go on before that.
