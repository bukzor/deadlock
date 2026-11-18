---
label: MELEE_DAMAGE
standing: open
why:
- stat-level.md
---

# Why does the data's melee damage differ from the owner's in-game numbers?

Light melee damage is 50-63 in hero data
(`m_mapStartingStats.ELightMeleeDamage`), and the owner's in-game table,
`docs/games/melee.txt`, reads 233-370 for quick melee. The gap is
recorded and unexplained. Level scaling
(`MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL`) is one candidate, a
multiplier elsewhere in the data another, and the table measuring
something else a third. An answer says which, and so whether melee
timelines are wrong at level 0 or only unscaled.
