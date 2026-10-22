---
name: office
description: Open the agents office, the live control room at http://localhost:3000/office that shows who is working, on what, and what came out.
disable-model-invocation: true
---

Start `python tools/office.py` (Mac: `python3`) **in the background**, so it doesn't block the session. Wait 2 seconds and check that it is running (for example `curl -s localhost:3000/api/state`). Then tell the user to open http://localhost:3000/office in the browser. If port 3000 is taken, use `python tools/office.py 3001`.
