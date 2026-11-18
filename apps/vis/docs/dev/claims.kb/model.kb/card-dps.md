---
label: CARD_DPS
standing: agent
why:
- cast-model.md
- level-scaling.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# A cast's card DPS is its DPS property at the total spirit power

`card_dps` is a cast's `DPS` property plus its spirit scaling, at the
`spirit` parameter plus what the hero's level adds, the same scaling the
model's ticks use. It is shown whenever the property exists: when the
ticks are not modeled (no duration or tick interval in the data), and
when it is 0 at the given spirit, because that is still the card's
number. Scaling by another stat is left out, as the cast's note says.

Overturned by hovering the ability in the sandbox at a known spirit power
and reading a different DPS. Built in
`apps/vis/server/src/vis_server/casts.py` (`card_dps`).

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md`.
