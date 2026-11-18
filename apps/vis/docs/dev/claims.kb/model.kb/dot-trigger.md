---
label: DOT_TRIGGER
standing: agent
why:
- ../original-request.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# A damage-over-time tick's trigger is the cast

Each tick of a cast's damage over time has the cast as its trigger, so
its bar spans from the cast to that tick. The request puts the
"triggering event" at a bar's left side, and for guns and melee that is
the player's input; a cast tick is the same, so trigger means one thing
across every source and a chart that mixes sources reads one way.
Declined: the start of the tick's interval (unit 005's first choice),
which tiles the duration neatly but makes trigger mean "when accrual
began" for casts alone.

This reads the owner's words, and only the owner can overrule the
reading; no in-game measurement bears on it. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md), *Model*. Built by
unit 010.
