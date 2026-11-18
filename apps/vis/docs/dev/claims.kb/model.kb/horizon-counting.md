---
label: HORIZON_COUNT
standing: agent
why:
- ../original-request.md
- ../../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-002-measures.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# A horizon total counts a hit when it lands

Total damage and first land count a hit only if it lands by the
horizon; a hit triggered before the horizon and landing after it is
left out. Time to kill is the land of the hit that reaches the target's
hp, wherever it falls. A stopwatch on a training dummy sees
damage when it lands, so this is the count the request's "checkable
in-game" can check. Unit 002 chose this; the coordinator adopted it.

It is a definition, chosen to match the check, so only a different
check would overturn it. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md), *Measures*.
