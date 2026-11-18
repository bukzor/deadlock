---
label: MELEE_LISTING
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# Melee is two pseudo-abilities, `melee_light` and `melee_heavy`

The `abilities` query lists melee as two pseudo-abilities, `melee_light`
and `melee_heavy`, beside the gun and the casts. Declined: an
`attack=light|heavy` parameter on `timeline`. The pseudo-abilities keep
the request's "character+ability" as the only choice a user makes: the
ability picker offers melee with no extra form field, and every damage
source answers the same `(hero, ability)` pair.

Design: [`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md),
*Protocol*. Built by unit 008.
