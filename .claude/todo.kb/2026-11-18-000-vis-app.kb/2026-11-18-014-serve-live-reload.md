---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - ./2026-11-18-013-legible-dot-and-downtime.md   # shares server/src/vis_server/
required-reading:
  - ./CLAUDE.md
  - ../../../apps/vis/README.md
  - ../../../apps/vis/bin/serve
  - ../../../apps/vis/server/src/vis_server/__main__.py
  - ../../../apps/vis/client/vite.config.ts
  - ../../../apps/vis/docs/dev/claims.kb/serve-command.md
---

# `bin/serve`: one command that reloads live, client and server

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 1)

## Problem Statement

The user asked, verbatim: "shouldn't the client auto-update? are we not using
vite?" Today `bin/serve` builds `client/dist` once and has the Python server
serve it. Live reload exists only as the README's two-terminal recipe.

Make `apps/vis/bin/serve` the live loop, in one command:
- the Vite dev server, with hot module reload, as the URL the user opens;
- `vis-server serve` under uvicorn's reload, watching the server sources and
  the `deadlock` package.

**Requirements:**
- Ctrl-C stops both processes, and neither outlives the script.
- The script prints the one URL to open. The user's Windows browser must reach
  it from WSL2, as unit 012 established; check it with `powershell.exe -c
  "curl.exe -s …"`.
- Keep the shim ≤50 lines (`~/.claude/must-read.kb/before/writing-bash-scripts.md`).
- Keep or drop the built-`dist` path, your call, and record the decision. If
  you keep it, it goes behind a flag.
- Update the README's "Run it" and "Develop it" sections to match.
- Update the `serve-command.md` claim's body. If its meaning changes, file a
  successor claim citing the user's words above, as unit 013 did for its
  claims.

**Proof** (the Final report quotes the observed output):
- Edit a client file and see the page change without a reload, using headless
  Chrome the way unit 012 drove it.
- Edit a server file and see `/api` answer from the new code.
- Revert both edits.

The user may have the old `serve` running on 8787. Never kill a process you
didn't start. If the port is taken, say so; don't take it.

**Scope:** `apps/vis/bin/*`, `apps/vis/README.md`,
`apps/vis/server/src/vis_server/__main__.py` and its `main_test.py`,
`apps/vis/client/vite.config.ts`, `apps/vis/client/package.json`,
`apps/vis/docs/dev/claims.kb/serve-command.md` (and a successor claim beside it)

## Steps

## Decisions

## Open Questions

## Final report
