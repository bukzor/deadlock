---
label: STAT_LEVEL
standing: agent
why:
- ../acceptance-bar.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# Stats are level 0 with no items

Every timeline uses the hero's level-0 stats with no items, and says so
in a note. Level scaling and items are deferred: `ACCEPTANCE` asks to
explore the data, and level 0 is the data as it is written, with no
scaling rule to guess. Adding a `level` parameter later changes the
inputs and none of the model.

Overturned when the owner needs a timeline at a given level, or when
`MELEE_DAMAGE` turns out to be level scaling. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md), *Model*.
