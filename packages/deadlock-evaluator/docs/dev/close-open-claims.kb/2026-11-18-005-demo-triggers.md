---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - CLAUDE.md
  - ../claims.kb/tooling.kb/local-demo-corpus-triggers.md
  - ../claims.kb/tooling.kb/public-match-demos-source.md
  - ../../../../docs/dev/environment.kb/game-install-paths.md
---

# `demo triggers`: what writes each file in the install's replays dir

**Parent:** <../close-open-claims.md> (wave 4)

## Problem Statement

Goal: close, or narrow to one owner observation, the open claim
`LOCAL_DEMO_TRIGGERS`: what creates `<match_id>.dem`, `auto-*.dem`, and
the `recent/`, `pending_upload/`, `discarded/` subdirectories under
`game/citadel/replays/`, and whether `auto-*` covers bot matches. The
owner asked for the exact triggers. Evidence available without playing:

- `data/dlls/convars.tsv` and `concommands.tsv` at the repo root: every row
  whose name or help mentions replay, demo, record, upload, highlight;
  defaults, flags, and which DLL declares it.
- Client config under `game/citadel/cfg/` (`*.vcfg`, `machine_convars.vcfg`
  and kin): which of those convars the owner's client has set, and the
  files' mtimes.
- Timestamps: birth/mtime of the three subdirectories and of the first
  `auto-*.dem` (2026-10-07) against the game's patch dates (git log of the
  committed build stamp under `data/`; Steam's `appmanifest_1422450.acf`
  `LastUpdated`) and against the `botmatch*.dem` dates (Oct 3-7).
- Demo headers: with boon (`data/tools/boon.d/bin/python -I`, see
  `event-volume-per-demo.py` beside the EVENT_VOLUME claim for the
  idiom), read one `auto-*.dem` of each size class (the 0.3 MiB ones and a
  full one): map, game mode, roster size, tick rate, server address if
  present. That decides client- vs server-side and bot vs public.
- Strings in `client.dll`/`server.dll` adjacent to `pending_upload` and
  `discarded` (plain `strings | grep -C3`), naming the feature they serve.

Write what is settled into the claim body (≤120 words; cite the TSV rows
by name; keep `standing: open` if any sub-question stays unresolved,
listing exactly what the owner must observe and how). The directory
facts (which file kinds, what makes them) go into the inventory section of
`game-install-paths.md`. Read the install only; never write under it.

**Scope (only these files):**
`../claims.kb/tooling.kb/local-demo-corpus-triggers.md`,
`docs/dev/environment.kb/game-install-paths.md` (repo root, inventory
section only), `trash/unit-005/**`, this file.

## Steps

- [ ] Grep the DLL TSVs; tabulate the replay/demo/record/upload rows.
- [ ] Read the client cfg files; note set values and mtimes.
- [ ] Collect timestamps (subdirectories, first `auto-*`, patch dates).
- [ ] Read headers of three `auto-*.dem`; compare with a `botmatch*.dem`.
- [ ] Grep DLL strings around the subdirectory names.
- [ ] Amend the claim and the inventory; validate; commit scope + this file.

## Decisions

## Open Questions

## Final report
