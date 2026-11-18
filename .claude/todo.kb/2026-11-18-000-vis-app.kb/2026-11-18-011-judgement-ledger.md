---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md
  - ../../../packages/deadlock-evaluator/docs/dev/   # the repo's precedent ledger: copy its shape
---

# `apps/vis/docs/dev/claims.kb/`: the coordinator's judgement calls, agent-signed

**Parent:** <https:../2026-11-18-000-vis-app.md> (cross-wave)

## Problem Statement

The user told the coordinator to make the open calls on its own authority,
following the user's inferred intent, to keep things simple where improving
them later is obviously possible, and to file each call as an agent-signed
claim. Their words are in session `14fac9c8-bc5e-42f7-956c-f88e2a8e613c`; find
the user message that contains "agent-signed claims" with `grep` in
`~/.claude/projects/-home-bukzor-claude-deadlock/14fac9c8-bc5e-42f7-956c-f88e2a8e613c.jsonl`.
Quote it *sensatim* as the ledger's one `standing: user` ground, plus the
user's original request, which is quoted in `../2026-11-18-000-vis-app.md`.
Load Skill(llm-claims-kb) and Skill(llm-claims), with the Skill tool, before
writing.

Build a ledger for `apps/vis`, modelled on the precedent at
`packages/deadlock-evaluator/docs/dev/`. Each claim below is
`standing: agent`, and its `why:` cites the user grounds and the design
section that implements it. Where a later in-game measurement would overturn
a claim, say so in its body.

The design doc stays the home of *what* is built. Each claim holds *that* it
was the agent's call, and *why*. Don't restate the design: link it.

Claims (coordinator's calls; word the labels and bodies yourself):
1. React + Vite over Vue/Nuxt: nothing needs SSR or routing, and Plot is
   framework-agnostic.
2. The server is its own uv workspace on 3.14. The user asked for the latest
   Python, and the root workspace stays on 3.12 for the extract tooling.
3. JSONL responses are built whole, not streamed, so an error can still set the
   status. Keeping it simple: streaming can come later, and the client already
   parses line by line.
4. Melee is listed as two pseudo-abilities, `melee_light` and `melee_heavy`, not
   as an `attack` parameter.
5. Melee wind-up isn't in the data, so it is a `windup` parameter that defaults
   to 0.
6. The cast model is a labelled heuristic: impact at the cast delay, ticks over
   the duration, repeat at the cooldown, plus spirit scaling. Simple, and fixed
   later by in-game evidence.
7. A damage-over-time tick triggers at the cast. That follows the user's "left
   side as triggering event", and `trigger` must mean the same thing for every
   source. Rejected: the interval start (unit 005's choice).
8. Bullet speed: the curve wins over `m_flBulletSpeed` when a gun has both, and
   the output notes the conflict as unverified (unit 003's choice, adopted).
   Settled by timing a shot in-game.
9. Stats are level 0 with no items, and level scaling is deferred. The
   acceptance bar is "I can open a browser and poke at my data". The melee
   damage in the data (50–63) doesn't match the user's `docs/games/melee.txt`
   (233–370); that is unexplained and recorded, not guessed at.
10. Horizon totals count a hit when it lands, matching a stopwatch on the dummy
    (unit 002's choice, adopted).
11. Ten damage-over-time abilities whose duration is in a nonstandard property
    stay unmodeled for now (unit 005).
12. Client tests are named `{module}.test.ts`, the vitest norm, instead of the
    house `_test` suffix (unit 006's choice, adopted).
13. The acceptance bar is met by one command that serves the built client and
    the API on localhost, where the user's Windows browser on WSL2 can reach it
    (wave 3 delivers this).

Run the ledger tools the skill names (graph, mentions, grounding) and
`llm.kb-validate` on it, clean.

**Scope (only these files):** everything under `apps/vis/docs/`

## Steps

- [x] read the precedent, the design, the session's two user messages (L5, L1002)
- [x] write the ledger under `apps/vis/docs/dev/`
- [x] run graph, mentions, grounding, `llm.kb-validate`; clean
- [x] self-audits; commit

## Decisions

- **Three `user` grounds, not one.** L1002 holds two rulings, the delegation
  (`OWN_AUTHORITY`) and the acceptance bar (`ACCEPTANCE`), and the original
  request (`VIS_REQUEST`, L5) is a ruling too. The grounding tool counts only
  `standing: user` claims as ground, so a request quoted in prose alone would
  leave every claim citing it ungrounded.
- **One sub-theory, `model`**, coining `Cycle`, `Hit`, `trigger`, `land`,
  `wind-up`, `horizon`; its claims share one overturner (an in-game
  measurement) and its own `stale-when:`. Stack and protocol calls coin
  nothing of their own, so they stay at the top (`VIS_APP`).
- **`todo: true`** on the calls not built yet: `MELEE_LISTING` (unit 008),
  `RESPONSE_BUFFERING` (009), `SERVE_COMMAND` (wave 3).
- **Added `MELEE_DAMAGE`, `standing: open`**: brief item 9's "unexplained and
  recorded" is an open question, so it is filed as one, apart from `STAT_LEVEL`.
- **"jdugements" emended to "judgements"** in the quote (a typo, per VOICE).
- `why:` cites the design doc by file; the section is named in the body.
  The graph tool reports those and the handoff citations as "reference into
  another ledger" on stderr; that is informational, not a dangling link.

## Open Questions

- Brief item 11 said ten abilities keep their duration in a nonstandard
  property. The survey in `casts.py` says nine do, and one has no tick
  interval. `UNTICKED_DOTS` states the survey's split.

## Final report

- `apps/vis/docs/dev/`: `claims.md` (VIS_APP) beside `claims.kb/`, with
  `model.md` beside `model.kb/`; 3 user, 15 agent, 1 open claims.
- `llm.kb-validate`: 19 files, 0 errors. `llm-claims-kb-mentions`: 0 tokens.
  `llm.kb-validate-links`: 25 links, 0 broken. Graph: 24 nodes, 1 component,
  acyclic. Grounding: every agent claim reaches a user ground; OWN_AUTHORITY
  carries 14.
- Deviations: the extra user grounds and `MELEE_DAMAGE` (Decisions); the
  nine-plus-one split (Open Questions).
