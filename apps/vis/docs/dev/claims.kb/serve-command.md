---
label: SERVE_COMMAND
standing: agent
todo: true
why:
- acceptance-bar.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# One command serves the built client and the API on localhost

`ACCEPTANCE` is met by one documented command that serves the built
client (`client/dist`) and the API from one process on localhost. The
owner's browser runs on Windows and the server in WSL2, which forwards
localhost ports to Windows by default, so the URL the command prints
opens there unchanged. Declined as the acceptance path: the Vite dev
server plus a separate API process, which is two commands and a proxy.
That pair stays the way to develop the client.

Design: [`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md),
*Shape*. Built in wave 3, which gives this claim a `verify:`.
