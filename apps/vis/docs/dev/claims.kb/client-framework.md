---
label: CLIENT_FRAMEWORK
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# The client is React on Vite

The client is Vite + React + TypeScript, as the request named first.
The request invited Vue, Nuxt "or whatever"; what Nuxt adds is
server-side rendering and file-based routing, and this app is one page
reading a JSONL API, so it would add nothing here. Observable Plot, the
chart library, renders plain DOM and binds to any framework, so it
pulls neither way.

Revisit when a view needs routing or server-side rendering. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Shape*.
