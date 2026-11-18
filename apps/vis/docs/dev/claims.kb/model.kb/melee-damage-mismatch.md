---
label: MELEE_DAMAGE
standing: open
why:
- level-scaling.md
---

# Why does the data's melee damage differ from the owner's in-game numbers?

Light melee damage is 50-63 in hero data
(`m_mapStartingStats.ELightMeleeDamage`), and the owner's in-game table,
`docs/games/melee.txt`, reads 233-370 for quick melee. Level does not
explain it: at the last level, 35, light melee reaches at most 118. Read
as heavy melee, only Paige's 233 fits a level (33); the other seven
readings need 47 to 73 boons
([`boons-per-level.md`](../../../../../../docs/dev/mechanics.kb/boons-per-level.md),
*The melee gap is not level*). Left: a multiplier elsewhere in the data,
or the table measuring something other than one swing's damage. An answer
says which, and so whether melee timelines are wrong at every level.
