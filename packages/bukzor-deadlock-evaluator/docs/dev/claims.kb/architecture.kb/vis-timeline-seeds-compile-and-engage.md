---
label: VIS_SEED
standing: agent
why:
- compile-is-pure-and-emits-breakpoints.md
- engage-starts-trivial.md
- measure-is-the-ground-truth-loop.md
- ../../../../../../docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
---

# The damage package's timeline is the seed of compile and the trivial engage

`bukzor-deadlock-damage` (`packages/bukzor-deadlock-damage/`; design:
`docs/dev/decisions.kb/vis-app.md` at the repo root, status proposed)
turns one hero's gun, melee or cast into a `Cycle` of
`Hit`s from the game data (`timeline.py`) and unrolls it over a horizon;
`measures.py` derives DPS and a time to kill against a given HP, each
with an in-game check string. That is compile for one attacker and
engage against a stationary target, with the measure loop already
named. The evaluator imports `bukzor-deadlock-damage` rather than
re-deriving it; vis imports the same package. What it lacks and the
evaluator adds: a defender (resistances, regen), items and ability
levels, a two-sided exchange.

The import edge is settled by the owner's package split
(`docs/dev/decisions.kb/small-bukzor-prefixed-packages.md`, commit
`5a1f8db`):

> [!@bukzor] 5a1f8db -- prefer small packages over too-large ones: a
> unit that *can* move cleanly into another package is significant
> enough to be held separate.
