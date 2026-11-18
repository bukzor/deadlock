---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-18-002-event-volume.md
required-reading:
  - CLAUDE.md
  - ../claims.kb/representation.kb/segmentation-from-events.md
  - ../claims.kb/representation.kb/typed-episodes.md
  - ../claims.kb/architecture.kb/situation-is-a-graded-episode-entry.md
  - ../claims.kb/tooling.kb/reuse-a-demo-parser.md
  - 2026-11-18-002-event-volume.md
---

# `segmentation`: cut one demo into fight episodes from damage events

**Parent:** <../close-open-claims.md> (wave 3)

## Problem Statement

Goal: close `SEGMENTATION` for fights. From the public demo's damage
events (hero-on-hero only), cluster in time and space: a gap longer than
G seconds or farther than R units starts a new episode. Sweep G over
{5, 10, 15} and R over {1500, 3000, none} and report episode counts and
median duration per setting. Pick the setting whose boundaries agree
with kill events (every kill inside an episode; no episode without
damage from both teams) and state the agreement rate.

Then assess rotations and farm windows: can they be told apart from
position tracks alone, at the position-update rate unit 002 measured?
Answer yes, no, or needs-a-trial with one sentence of reason.

Rewrite `segmentation-from-events.md`: fights measured (`standing:
bare`, `verify:` the script), the rest as an `agent` sentence. Script
and outputs stay in `trash/unit-004/`; if the script is worth keeping,
say so in Open Questions and the coordinator will place it.

**Scope (only these files):** `../claims.kb/representation.kb/segmentation-from-events.md`;
this file; `trash/unit-004/`.

## Steps

## Decisions

## Open Questions

## Final report
