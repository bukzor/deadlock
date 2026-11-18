---
label: DOT_TILING
standing: agent
why:
- ../original-request.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# Damage-over-time ticks tile their duration

A damage-over-time tick's trigger is the previous tick's land; the first
tick's trigger is the cast. Each bar then spans the interval in which
its tick's damage builds, and the bars sit side by side across the
duration, readable at a glance. Declined: every tick triggered at the
cast (`DOT_TRIGGER`), which stacked the bars from t=0 into a staircase
the owner could not read:

> [!@bukzor] 14fac9c8#L1273
> I have to say I don't understand the result though.
> What's with the shading?

For guns and melee, trigger stays the player's input; for a tick it is
when that tick's damage starts building. Only the owner can overrule
the reading; no in-game measurement bears on it. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md),
*Model*; built in `apps/vis/server/src/vis_server/casts.py`.
