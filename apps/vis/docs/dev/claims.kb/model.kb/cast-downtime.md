---
label: CAST_DOWNTIME
standing: agent
why:
- uptime-every-source.md
- cast-model.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# A cast's downtime is the cooldown left after its last land, floored at 0

A `Cycle` carries its downtime, the seconds of each period spent
dealing no damage, and `uptime_dps` divides a cycle's damage by its
period less that downtime (`UPTIME_ANY_SOURCE`). Per source:

- **gun:** the reload, so `uptime_dps` stays the stat panel's DPS;
- **melee:** 0;
- **cast:** the cooldown left after the last land.

When a cast's damage outlasts its cooldown, the downtime is 0 and a
note says that casts on cooldown overlap: back-to-back casts keep the
target taking damage the whole period, so the period is all uptime.
Declined: a negative downtime, which would divide by more than the
period. A cast with no cooldown happens once and has downtime 0.

Overturned by timing, in the sandbox, how long one cast keeps damaging
the training dummy. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md),
*Model* and *Measures*; built in `packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/casts.py`.
