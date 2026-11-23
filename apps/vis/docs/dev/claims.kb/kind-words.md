---
label: KIND_WORDS
standing: agent
why:
- model.kb/uptime-every-source.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# Each kind's measures carry its own labels and one-sentence checks

Labels by kind: "Damage per clip / cast / swing"; "DPS incl. reloads",
"DPS incl. cooldown", and plain "DPS" for melee, whose period has no
downtime; `uptime_dps` is "DPS while firing (weapon panel)" for a gun and
"DPS from cast to last damage" for a cast. Every check is one sentence
built from the kind's own actions (empty a clip, cast on each cooldown,
swing nonstop) at the sandbox training dummy, and the stopwatch starts on
the kind's input (first shot, the cast, first swing).

`uptime_dps` is still computed alike for every source
(`model.kb/uptime-every-source.md`), but its check differs: a gun's reads
the weapon's stat panel, which shows that very number, and a cast's times
one cast to its last damage. Declined: one shared check for all kinds,
which the review found was the page's widest and most repetitive block.
Overturned if the owner reads `UPTIME_ANY_SOURCE` as one check text, or if
the stat panel's DPS turns out to differ from `uptime_dps`. Built in
`packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/measures.py`.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md`; `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md`.
