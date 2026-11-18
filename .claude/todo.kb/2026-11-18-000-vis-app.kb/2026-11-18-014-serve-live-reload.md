---
managed-by: Skill(llm-subtask)
status: done
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

- [x] `vis-server serve --reload` (uvicorn import-string factory, watching `vis_server/` and `deadlock/`), tested
- [x] `vite.config.ts` proxy target from `$VIS_API` (default unchanged)
- [x] `bin/serve` rewritten as the live loop (48 lines)
- [x] README "Run it"/"Develop it"; `serve-command.md` superseded by `serve-live-reload.md` (`SERVE_LIVE`)
- [x] Proof in headless Windows Chrome over CDP; both edits reverted

## Decisions

- **Ports:** Vite (the URL) on `PORT`, default 5173; the API on `API_PORT`, default 8788. Not 8787, so it
  never collides with the user's old `serve`. A taken port aborts with a message; nothing is killed.
  `--strictPort` stops Vite silently moving.
- **Built-`dist` path dropped** from `bin/serve`, no flag: one command, one loop. `pnpm run build` plus
  `vis-server serve` still serves `dist` (documented in the README). Recorded as `SERVE_LIVE`; the old
  claim is marked superseded.
- **No global pnpm needed:** `bin/serve` runs `client/node_modules/.bin/vite` directly; `pnpm` is called
  only when `node_modules` is missing or older than the lockfile.
- **Cleanup:** `set -m` gives each child its own process group; an EXIT trap kills both groups.
- **Port probe** is `timeout 1 bash -c '</dev/tcp/...'` because in this sandbox a connect to a closed
  port hangs instead of refusing.

## Open Questions

- The 8788/5173 defaults are my pick; the README had 8787 as the one port.
- `bin/serve` no longer builds `dist`, so nothing exercises `tsc --noEmit` on launch; `pnpm run check` does.

## Final report

Checks: server `pytest` and basedpyright clean; the `--reload` test fails with `reload=False` (mutation
observed). Port 8787 taken: `PORT=8787 bin/serve` printed `vis: port 8787 is taken ...`, exit 1.
Proof (`trash/014/prove.mjs`, page kept open, `window.__marker` set):
```
before client edit: h1 = Damage over time
after client edit:  h1 = Damage over time (LIVE-EDIT) | window.__marker = no-reload
before server edit: /api/heroes line 1 = {"hero":"hero_artist","name":"Violet"}
after server edit:  /api/heroes line 1 = {"hero":"hero_artist","name":"Violet","proof":14}
```
`powershell.exe -c "curl.exe -s http://localhost:5173/api"` returned the API listing; `/` returned Vite's
HTML. SIGINT and SIGTERM each left no `vite`/`uvicorn`/`serve` process; the user's 8787 server was untouched.
Edits to `App.tsx` and `queries.py` were reverted (empty `git diff`). No pnpm used at all.
