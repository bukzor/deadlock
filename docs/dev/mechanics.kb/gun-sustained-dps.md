# Gun sustained DPS

DPS averaged over a full clip and its reload — what a gun deals over time, as
opposed to the UI's DPS (`./gun-fire-rate.md`), which stops at the reload.

Extra fields, from the same `m_mapWeaponInfos.primary`: `m_iClipSize`,
`m_iAmmoConsumedPerShot` (unset means 1), `m_reloadDuration`,
`m_bReloadSingleBullets`, `m_flReloadSingleBulletsInitialDelay`.

```
ammo'   = ammo_per_shot or 1
shots   = clip / ammo'
reload' = initial_delay + clip × reload    if reload_single_bullets
          reload                           otherwise
sdps    = damage × pellets × shots / (shots / bps + reload')
```

- Ammo per shot is set above 1 only on secondaries (Shiv's alt 4, Yamato's 3,
  Viscous's 5), leaving them 2–3 shots per clip.
- With single-bullet reload (Abrams, Silver), `m_reloadDuration` is per shell.

**Unverified:** the game shows no sustained DPS, so this is checked only through
its inputs. The single-shell `reload'` (Abrams: 0.705 + 9 × 0.3525 = 3.88 s)
assumes a reload from empty refills every shell; compare the UI's reload time.
The UI's reload matches `m_reloadDuration` for magazine guns (Seven 2.35, Paradox
2.58, Lash 2.35, Sinclair 2.5).
