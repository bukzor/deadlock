---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - ./2026-11-18-026-names-and-hp-zoom.md   # it may close Later items; list only what remains
required-reading:
  - ./CLAUDE.md
  - ../../ideas.kb/CLAUDE.md   # where each entry goes, and the tool that creates it
  - ../2026-11-18-000-vis-app.md   # its "Later" list
  - ./2026-11-18-028-maintainability-review.md   # Final report: the risks
  - ./2026-11-18-020-ux-review-2.md   # Final report: finding 1 awaits the user
  - ./2026-11-18-026-names-and-hp-zoom.md   # what it closed, and its Open Questions
---

# Wrap-up: known future improvements, one `.claude/ideas.kb/` entry each

**Parent:** <https:../2026-11-18-000-vis-app.md> (wrap-up)

## Problem Statement

The user: "list 'known future improvements' somewhere in an appropriate kb".
The plan and its handoff files are about to be retired, so every improvement
still open needs a durable home. That home is `.claude/ideas.kb/`, one entry per
improvement, created the way its CLAUDE.md says.

Sources, with each item closed by later work dropped:

- the plan's "Later" list;
- 028's risks 1–5, each with its smallest fix (risk 6 says "no action now", so
  leave it out);
- two more risks the coordinator found: `client/src/protocol.ts` mirrors the
  Python line shapes by hand, and nothing checks the two against each other;
  and player-facing wording (labels, checks, notes) lives inside the modelling
  modules;
- 020's finding 1 (a cast's default window), marked as awaiting the user's
  ruling against their "default 2 periods";
- any Open Questions in 026 and 027 that are improvements rather than
  questions.

Each entry stands alone: what is wrong or missing, the evidence (paths), and
the smallest known fix. It names the handoff file it came from as provenance,
by path and commit (`git show <commit>:<path>`), because those files will be
removed. Then replace the plan's "Later" list with one line pointing at
`.claude/ideas.kb/`.

**Scope:** `.claude/ideas.kb/*`, and the plan's "Later" section only.

## Steps

- [x] Drop closed items; create one `ideas.kb/` entry per open improvement
- [x] Replace the plan's "Later" list with a pointer

## Decisions

- Closed, so dropped (checked in code): `uptime_dps` on a single-hit cast
  (`measures.py` omits it), the cumulative-damage line (`chart.ts`), ability
  display names (026). 020's findings 2-8 were closed by 021-025.
- 020's gun-distance question is folded into the default-window entry.
- Upgrade-note casing (026) and round 1's "raw upgrade notes" are one entry.

## Final report

15 entries, `.claude/ideas.kb/2026-11-18-0{00..14}-vis--*.md`; the plan's
"Later" is now one line. Each entry cites its source file by path and commit.
