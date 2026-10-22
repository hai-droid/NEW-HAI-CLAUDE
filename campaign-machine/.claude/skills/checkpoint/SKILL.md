---
name: checkpoint
description: Save a stable point (checkpoint) of all the work, or go back to an earlier one (reset). Uses git.
argument-hint: [save <message> | list | reset <commit>]
disable-model-invocation: true
---

Checkpoint management: $ARGUMENTS

- `save <message>` (the default): `git add -A && git commit -m "checkpoint: <message>"`. If it isn't a git repo yet, run `git init` first. `.gitignore` already keeps out `.env`.
- `list`: `git log --oneline -15`, explained in Hebrew (what is in each point).
- `reset <commit>`: first show what will change (`git diff --stat <commit>`) and ask for explicit approval. Then save the current state as a branch (`git branch backup-<date>`), and only then run `git reset --hard <commit>`.

Note: going back here only rolls back the files on the computer. It does not change anything that was already created in Meta.
