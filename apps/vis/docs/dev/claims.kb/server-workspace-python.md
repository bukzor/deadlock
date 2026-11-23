---
label: SERVER_PYTHON
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
- ../../../../../docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
---

# The server is its own uv workspace on Python 3.14

`apps/vis/server/` is a uv workspace of its own, pinned to 3.14. The
request asked for the latest Python, and the root workspace pins 3.12
for the extract tooling, so the server cannot join the root workspace
without inheriting that pin. It still reuses the root `bukzor-deadlock`
package, as an editable path dependency.

The damage model it serves is not the server's: it is
`bukzor-deadlock-damage`, a root-workspace package on 3.12+, which the
server takes as another editable path dependency and the
bukzor-deadlock-evaluator imports too
([`vis-timeline-seeds-compile-and-engage.md`](../../../../../packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/vis-timeline-seeds-compile-and-engage.md)).
The owner's package split puts it there
([`small-bukzor-prefixed-packages.md`](../../../../../docs/dev/decisions.kb/small-bukzor-prefixed-packages.md)):

> [!@bukzor] 5a1f8db -- prefer small packages over too-large ones: a
> unit that *can* move cleanly into another package is significant
> enough to be held separate.

So the server's own pin costs nothing but its own code, which is the
protocol alone; the edge points one way, from 3.14 into 3.12+.
Revisit when the extract tooling runs on 3.14. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Shape*.
