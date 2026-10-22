---
name: new-client
description: Open a new client (or a new product of your own) as its own folder, and run the interview that fills in its business, brand voice and config. Use when the user wants to add a client, business or product.
argument-hint: <client-slug> [website-url]
disable-model-invocation: true
---

Open a new client folder: $ARGUMENTS

1. The first argument is the folder name: English, lowercase, digits and dashes (e.g. `yoga-tlv`). If it's missing or invalid, suggest one.
2. Copy `clients/_template/` to `clients/<slug>/`. Never overwrite an existing folder.
3. If a website was given, read it with WebFetch and pre-fill whatever you can: the offer, prices, audience, tone and real testimonials. Mark every pre-filled item with `(מהאתר – לאמת)`.
4. Interview the user in Hebrew to complete the three files. Ask in short rounds of 3–4 questions, not a wall of questions:
   - `business.md`: what is sold, to whom, the price, what makes it different, real proof (numbers, testimonials, clients), common objections, what we must never say.
   - `brand-voice.md`: 3 adjectives for the voice, formal or casual, gendered address (masculine / feminine / plural), words we love and words we never use, and 2–3 real examples of the brand's writing.
   - `config.json`: brand colors (hex, dark → main → accent), logo (ask them to put it in `clients/<slug>/assets/logo.png`), budget caps (`max_daily_budget`, `max_total_budget`, currency), and the Meta IDs if they have them already (ad account, page, pixel, Instagram). Leave unknown IDs empty and point them to the "חיבור Meta" section in the README.
5. Never invent facts. Anything unknown stays as a clear `TODO` in the file.
6. Finish with a summary of what was filled in, what is still missing, and the next step: `/campaign <slug> <what the campaign is for>`.
