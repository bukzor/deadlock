---
label: ABILITY_NAMES
standing: agent
why:
- melee-listing.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# Abilities and properties carry the game's English names, else the key

The `abilities` query names each ability by its token in the game's English
localization, read from the install (`citadel_heroes` and
`citadel_attributes`), and by its key when the game has none (a few
guns). The pseudo-abilities are "Light
Melee" and "Heavy Melee", the game's own labels for the two melee stats.
A cast's notes label a property by `{token}_label`, following the
property's `m_strLocTokenOverride`, as the game's tooltips do. When the
game has no label (127 of the 1038 upgrade properties of the live
signatures), the note falls back to the key in lower-case words.
Declined: the key itself as the fallback in notes, which puts an engine
name in player text. Overturned if the owner wants one casing throughout.
Built in `packages/bukzor-deadlock-lookup/src/bukzor_deadlock_lookup/names.py`;
the melee pseudo-names are `melee.NAMES` in
`packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/melee.py`.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md`.
