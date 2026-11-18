---
label: BULLET_SPEED
standing: agent
why:
- ../judge-on-own-authority.md
- ../../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-003-guns.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# Where a gun's bullet-speed curve and field disagree, the curve wins

Travel time uses `m_BulletSpeedCurve` where a gun has one and
`m_flBulletSpeed` otherwise, and where both exist and disagree the
output notes the conflict as unverified. Every live gun sets the field;
six also carry a curve, and on five of those the two disagree (Silver:
curve 571.5 m/s, field 812.8 m/s). The curve is the more specific
property, so it is the better guess at what the game reads. Unit 003
chose this; the coordinator adopted it.

Settled by timing a shot's travel in-game on one of the five guns.
Design: [`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md), *Model*,
Gun.
