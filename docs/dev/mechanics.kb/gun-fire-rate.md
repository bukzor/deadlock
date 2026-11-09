# Gun fire rate and DPS

Fields, from a gun's `m_mapWeaponInfos.primary`:
`m_flBulletDamage` (damage per pellet), `m_iBullets` (pellets per shot),
`m_iBurstShotCount` (shots per burst), `m_flCycleTime`,
`m_flIntraBurstCycleTime`.

```
intra' = intra if burst > 1 else 0
bps    = burst / (cycle + burst × intra')     # the UI's "bullets per second"
dps    = damage × pellets × bps               # the UI's "DPS": until reload
```

- A burst gun waits `intra` after *every* shot of the burst, the last one
  included, then `cycle`. `(burst − 1) × intra` — the intuitive count of gaps
  *between* shots — misses all four burst guns by 12–17%.
- A single-shot gun ignores `intra` even when it is set (Paige 0.1, Solomon
  0.075, The Doorman 0.05, Rat King 0.1). No unconditional formula fits both
  groups; the branch is the game's, not an artifact of the algebra.
- "Bullets per second" counts shots, not pellets; pellets multiply damage only.
- The UI's DPS excludes reload; see `./gun-sustained-dps.md` for the version that
  doesn't.

## Evidence

In-game hero stats, level 0, no items, build 6854 (2026-11-05):

| hero | burst | cycle | intra | pellets | damage | bps (UI) | dps (UI) |
|---|---|---|---|---|---|---|---|
| Seven | 3 | 0.2625 | 0.084 | 1 | 10.8 | 5.83 | 63 |
| Paradox | 5 | 0.294 | 0.0735 | 1 | 6.8 | 7.56 | 51 |
| Lash | 3 | 0.2625 | 0.084 | 1 | 8.46 | 5.83 | 49 |
| Sinclair | 2 | 0.525 | 0.105 | 1 | 16.5 | 2.72 | 45 |
| Paige | 1 | 0.5 | 0.1 | 1 | 32 | 2 | 64 |
| Solomon | 1 | 0.5 | 0.075 | 1 | 25 | 2 | 50 |
| The Doorman | 1 | 0.63 | 0.05 | 1 | 24 | 1.59 | 38 |
| Rat King | 1 | 0.2 | 0.1 | 2 | 5.8 | 5 | 58 |
| Abrams | 1 | 0.63 | 0 | 9 | 3.78 | 1.59 | 54 |

The formula reproduces every row to the UI's precision.
