---
label: SERVE_LIVE
standing: agent
why:
- acceptance-bar.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# One command serves the live loop: Vite with hot reload, over a reloading API

`ACCEPTANCE` is met by one documented command, `apps/vis/bin/serve`, that
runs the Vite dev server (hot module reload) and `vis-server serve
--reload` (uvicorn restarts on a change to the server or `bukzor_deadlock`
sources), and prints the one URL to open: Vite's, which proxies `/api` to
the server. Ctrl-C stops both. The owner's browser runs on Windows and the
server in WSL2, whose mirrored networking makes that URL open there
unchanged. Declined: serving the built `client/dist` from the Python
server as the command's path (`SERVE_COMMAND`), which showed stale code
until a rebuild:

> [!@bukzor] 14fac9c8#L1338
> shouldn't the client auto-update? are we not using vite?

The built path is dropped from `bin/serve`, not hidden behind a flag:
`pnpm run build` plus `vis-server serve` (no `--reload`) still serves
`client/dist`, the one-process shape, for anyone who wants it. The live loop
offers one page, so `serve --reload` never mounts `client/dist` (`GET /` is a
404 `{"error"}` line naming the API-only server), and the output's one URL
is Vite's: `bin/serve` filters uvicorn's "running on" banner and prints its
"open" line once both children listen. A stale `dist` had been opened on the
API's port. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Shape*;
built in `apps/vis/bin/serve`.
