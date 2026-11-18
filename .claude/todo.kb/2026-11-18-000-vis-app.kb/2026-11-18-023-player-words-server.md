---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Measures" (rewritten for this unit), "Protocol"
  - ./2026-11-18-020-ux-review-2.md   # Final report: findings 3, 4, 6, 8 are this unit's
  - ../../../apps/vis/server/src/vis_server/
---

# Server: measures and labels in the player's words, hp answered first, a clean hero list

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 3)

## Problem Statement

UX review round 2's findings 3, 4, 6 and 8 are server work. The design doc's
"Measures" section now states the decided outcome. Make the code match it:

- `time_to_kill` comes first when `hp` is given. With `hp` and no `horizon`,
  the default horizon stretches to the time-to-kill land, up to 120 s, but never
  below 2 periods. When the hp is still not reached, the note says so, as now.
- `uptime_dps` is omitted where it equals `steady_dps` (downtime 0) as well as
  for a single hit.
- `card_dps`: for a cast whose ability has a card DPS (its `DPS` property), the
  value at the given spirit and level. Label it so a player recognises the
  card's number.
- `average_dps` is gone.
- Labels and `check` text by kind: no label or check names another kind ("≈
  stat panel for guns", "(a clip, a swing, a cast)"). Keep each check short,
  one sentence a player can follow in the sandbox.
- `heroes`: sorted by display name, without `in_development` heroes
  (`heroes.tsv`) or the training dummy.

File each judgement call you make as an agent claim in
`apps/vis/docs/dev/claims.kb/` (see its CLAUDE.md).

**Scope:** `apps/vis/server/src/vis_server/*` and `apps/vis/docs/dev/claims.kb/**`.
`apps/vis/client/src/protocol.ts` too, only if a line's shape changes; a
new measure `name` needs no client change.

**Servers:** use your own ports for any proof run, and kill only the pids you
started. A `pkill -f` pattern kills the user's serve on 5173/8788.

## Steps

- [x] Read the inputs
- [x] Measures: `time_to_kill` first, `card_dps`, no `average_dps`, `uptime_dps` only with downtime, labels and checks by kind (`measures.py`, `Kind` in `types.py`)
- [x] Default horizon stretched to the time-to-kill (`measures.default_horizon`, used by `queries.timeline`)
- [x] `card_dps` from the cast's `DPS` (`casts.card_dps`)
- [x] `heroes`: by display name, no `in_development`, no dummy (`queries.listed`)
- [x] Claims filed; checks clean; commit

## Decisions

- Horizon with `hp`: whole periods (whole seconds for a one-shot) past the kill's land, 2-period floor, 120 s cap; 120 s when unreached, so the note says "within 120 s". Claim `KILL_HORIZON`.
- `card_dps` is the `DPS` property at total spirit (parameter plus level), shown even when the ticks aren't modeled or it is 0. Claim `model.kb/card-dps.md`.
- Wording per kind, and a gun's `uptime_dps` check reads the weapon's stat panel. Claim `KIND_WORDS`.
- Left-out heroes still answer `abilities`/`timeline` by key. Claim `HERO_LIST`.
- `AVERAGE_DPS_KEPT` struck (`verdict: superseded`); `HORIZON_DEFAULT` now scoped to "no hp".

## Open Questions

- Violet (`hero_artist`) is `in_development` in `heroes.tsv`, so she leaves the picker with Generic Person. The review listed her as a normal entry. Does the user want her back?
- `UPTIME_ANY_SOURCE` (a user claim) says "one in-game check for all three". The brief asks for checks by kind, so the checks now differ. The user's quoted words only ask to generalize the measure, so I read the claim's "one check" as agent text.
- `queries_test.py` is 315 lines, over the 300 limit (it was 287). Splitting it would break the `{module}_test.py` convention. I left it over.

## Final report

- Checks: `uv run pytest` passes (all server tests). `uv run basedpyright src` reports 0 errors. No client change: line shapes are the same, and only `protocol.ts`'s `hp` comment names a measure. Mutation runs on `default_horizon`, `card_dps`, the uptime rule and the card wiring each turned a named test red.
- Deviation: while the stubbed `measures(kind=...)` signature was saved and the caller wasn't yet updated, the live server 500'd. The coordinator flagged it, and by then the caller was already updated; the live API answered 200.
- Real data: Infernus gun, hp 600: the horizon grows to 5 periods (25.4 s) and `time_to_kill` is 20.4 s, listed first. Abrams `citadel_ability_bull_heal`: `card_dps` 22 equals `uptime_dps` 22. `heroes` lists 42, by name.
- Code: `apps/vis/server/src/vis_server/{measures,casts,queries,types}.py` and tests. Claims: `apps/vis/docs/dev/claims.kb/{kill-horizon,kind-words,hero-list}.md`, `model.kb/card-dps.md`, and amended `average-dps-kept.md`, `horizon-default.md`.
