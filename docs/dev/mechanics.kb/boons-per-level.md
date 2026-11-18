# Hero level: one boon per level-up

Fields, from a hero in `heroes.vdata`: `m_mapLevelInfo` (per game level 1..36,
`m_bUseStandardUpgrade`), `m_mapStandardLevelUpUpgrades` (what one boon adds),
`m_mapStartingStats.E{Light,Heavy}MeleeDamage`.

Level is numbered as `data/gamedata.tsv/levels.tsv` numbers it: game level − 1,
so level 0 is the 600 starting souls and level 35 the last. Every game level
from 2 sets `m_bUseStandardUpgrade`, so the boons at level N are N.

```
bullet  = m_flBulletDamage + N × BASE_BULLET_DAMAGE_FROM_LEVEL     # per pellet
light   = ELightMeleeDamage + N × BASE_MELEE_DAMAGE_FROM_LEVEL
heavy   = EHeavyMeleeDamage × light / ELightMeleeDamage
spirit  = N × TECH_POWER                                           # before items
```

(`MODIFIER_VALUE_` prefixes dropped.) Heavy melee grows in proportion to light:
the one melee field scales both attacks by the same factor.

- Per boon, on the 46 live heroes (build 6860): melee 1.58 on 41 (Abrams
  1.738, Venator 1.7, Paige and Violet 1.2, Baba 0.63); spirit power 1.1 on 39
  (Haze 0.5, Mo & Krill 0.6, Ivy 1.2, Kelvin, Sinclair and Viscous 1.3, Grey
  Talon 1.6); bullet damage varies per hero, 0 to 1.25.
- A boon also adds health (`BASE_HEALTH_FROM_LEVEL`); a few heroes' boons add
  resists or attack range. None of these changes the damage dealt.
- `BASE_BULLET_DAMAGE_FROM_LEVEL_ALT_FIRE` is set on 7 heroes; it applies to an
  alt fire, not to the primary gun.
- Spirit power gained from boons also feeds a hero's own spirit scaling
  (`m_mapScalingStats`): bullet damage on Vindicta (0.022), Grey Talon (0.08)
  and Solomon (0.14), heavy melee on Paige (0.45). How that scale
  applies is not settled here.

## The melee gap is not level

The owner's in-game table (`docs/games/melee.txt`, level unknown) reads
233-370 for quick melee. The formula above, at the last level (35), gives at
most 118 light melee (Viscous) and 274 heavy (Venator). Boons each reading
would need, as light or as heavy melee:

| hero | light, heavy (data) | per boon, light and heavy | quick melee (owner) | boons as light | as heavy |
|---|---|---|---|---|---|
| Abrams | 50, 116 | 1.738, 4.03 | 307 | 148 | 47 |
| Apollo | 63, 116 | 1.58, 2.91 | 327 | 167 | 73 |
| Bebop | 63, 116 | 1.58, 2.91 | 327 | 167 | 73 |
| Billy | 50, 116 | 1.58, 3.67 | 291 | 153 | 48 |
| Drifter | 51.5, 120 | 1.58, 3.68 | 370 | 202 | 68 |
| Paige | 42, 120 | 1.2, 3.43 | 233 | 159 | 33 |
| Rem | 58, 116 | 1.58, 3.16 | 314 | 162 | 63 |
| Viscous | 63, 116 | 1.58, 2.91 | 327 | 167 | 73 |

Only Paige's reading fits a level (33, as heavy melee); the other seven need 47
or more boons. Level does not explain the gap.

## Evidence

Unverified in-game. The formulas read the fields at face value. deadlock.wiki's
hero pages (fetched 2026-11-18) show the same numbers per boon, including the
heavy-melee rule: Abrams light +1.74 and heavy +4.03 (1.738 × 116/50), Bebop
light +1.58 and heavy +2.91 (1.58 × 116/63), bullet damage +0.1 (Abrams) and
+0.115 (Bebop) per pellet, spirit power +1.1. The wiki's numbers may come from
the same files, so they corroborate the reading, not the game. Its Boon page says every
level-up grants one, and that the last is 35. To check in-game: in the sandbox,
read the stat panel's bullet and melee damage at level 0 and after N level-ups.
