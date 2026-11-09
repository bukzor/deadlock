# Cooldowns by ability kind

Every bound ability carries an `AbilityCooldown` property, but only cast
abilities use it. Guns and melee set it to 0 and rate-limit elsewhere — so a
`0` there is not "no cooldown".

| kind (`m_eAbilityType`) | rate limit | where |
|---|---|---|
| Signature, Ultimate, Innate | `AbilityCooldown` (charges: `AbilityCharges`, `AbilityCooldownBetweenCharge`) | `m_mapAbilityProperties.*.m_strValue` |
| Weapon (guns) | `m_flCycleTime`, `m_flIntraBurstCycleTime` — see `./gun-fire-rate.md` | `m_mapWeaponInfos.<profile>` |
| Melee | `m_flCooldownOnHit`, `m_flCooldownOnMiss`, per attack | `m_mapAttacks.EAttackType_{Light,Heavy,HeavyAir,Slide}` |

Melee as of build 6854: Light 0.75 s on hit and miss (one hero 0.65); Heavy and
HeavyAir 1.0 on hit, 1.3 on miss; Slide 1.0. Melee damage is per hero, not per
attack: `ELightMeleeDamage` / `EHeavyMeleeDamage` in `heroes.vdata`. That Heavy
damage also applies to HeavyAir and Slide is inferred, not checked.

Cast abilities have no single DPS: damage lives in bespoke properties (`Damage`,
`DPS`, `ImpactDamage`, `PulseDamage`, ...; 24 of 184 signatures have none), and
charges, channels, and spirit scaling defeat one damage-over-cooldown formula.
