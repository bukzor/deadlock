---
label: SERVER_PYTHON
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# The server is its own uv workspace on Python 3.14

`apps/vis/server/` is a uv workspace of its own, pinned to 3.14. The
request asked for the latest Python, and the root workspace pins 3.12
for the extract tooling, so the server cannot join the root workspace
without inheriting that pin. It still reuses the root `bukzor-deadlock`
package, as an editable path dependency.

The cost: the bukzor-deadlock-evaluator, which sits in the root workspace,
cannot import the timeline until one side moves
([`vis-timeline-seeds-compile-and-engage.md`](../../../../../packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/vis-timeline-seeds-compile-and-engage.md)).
Revisit when the extract tooling runs on 3.14. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Shape*.
