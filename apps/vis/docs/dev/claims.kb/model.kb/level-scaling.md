---
label: LEVEL_SCALING
standing: agent
why:
- hero-level.md
- ../acceptance-bar.md
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/mechanics.kb/boons-per-level.md
---

# A level adds one boon per level-up, read at face value

Level N is numbered as `data/gamedata.tsv/levels.tsv` numbers it, 0 to 35,
and grants N boons. A boon adds the hero's per-boon bullet damage to each
pellet, its per-boon melee damage to light melee (heavy melee by the same
factor), and its per-boon spirit power. The `spirit` parameter is spirit
power on top of the level's, so `spirit` 0 at level 10 is the level's
spirit alone. A level outside 0 to 35, or not a whole number, is a 400.
Above level 0 a note lists what the boons add and says it is not checked
in-game. Formulas and evidence:
[`boons-per-level.md`](../../../../../../docs/dev/mechanics.kb/boons-per-level.md).

Declined: modeling the hero's own spirit scaling of bullet or heavy-melee
damage (four heroes), whose form the data does not settle; a note names
it whenever the level's spirit is above 0. Declined: `spirit` as the total
spirit power, which would make the level's spirit silently vanish whenever
a user typed a value.

Overturned when the stat panel, after N level-ups in the sandbox, shows
bullet or melee damage other than these formulas give.
