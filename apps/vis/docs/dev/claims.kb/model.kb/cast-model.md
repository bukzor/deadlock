---
label: CAST_MODEL
standing: agent
why:
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# The cast model is one labelled heuristic for every ability

Every signature and ultimate with damage goes through one heuristic:
impact at the cast delay, ticks across the duration, a repeat at the
cooldown, plus spirit scaling. Each cast timeline says in a note that
it is an unverified heuristic, and names the charges, upgrades and
level scaling it skips. Declined: a model per ability, which needs
knowledge of each ability that the data does not encode in one shape.
The heuristic is the simple option `OWN_AUTHORITY` allows, because
correcting it ability by ability later is plainly possible.

Overturned, one ability at a time, by timing a cast against a training
dummy. Design: [`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md),
*Model*, Cast; the fields are in
`apps/vis/server/src/vis_server/casts.py`.
