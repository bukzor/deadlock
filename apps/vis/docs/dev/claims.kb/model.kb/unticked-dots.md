---
label: UNTICKED_DOTS
standing: agent
why:
- cast-model.md
---

# Ten damage-over-time abilities are noted, not modeled

Ten of the 24 casts with `DPS` get no ticks: nine keep their duration
in an ability-specific property (`BurnDuration`, `DebuffDuration`, ...)
and one has no tick interval. Their timelines carry a note naming the
candidate properties instead. Declined: growing `CAST_MODEL` to guess
which property governs the ticks, which would chart invented damage.
Unit 005 chose this; the coordinator adopted it.

Overturned by reading each of the ten abilities, which is a later unit.
The survey is in `packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/casts.py`'s docstring.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-005-casts.md`.
