---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.md (Problem Statement: all the owner's rulings)
  - docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md
  - docs/dev/environment.kb/whisper-asr.md
  - src/bukzor_deadlock/vo_asr.py, vo_asr_batch.py, vo_asr_ledger.py, vo_asr_view.py (+ tests)
  - data/vo/japanese.tsv.do, bin/asr-start
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.kb/2026-11-24-006-fixups.md (Decisions: the fix-up conventions to follow)
---

# `other languages`: every "Speaks <language>" clip, not only Japanese

**Parent:** <https:../2026-11-24-000-vo-transcripts.md> (wave 7)

## Problem Statement

The owner has extended the plan beyond Japanese. In `data/vo/lines.tsv`,
Ivy (`tengu`) has 34 clips captioned "Speaks spanish", and Lady Geist
(`ghost`) and Bebop have one "Speaks French" clip each. They should get the
same treatment as Yamato's Japanese clips.

1. **The language comes from the caption.** The scope becomes every clip
   whose caption matches "Speaks <language>" (case-insensitive), with
   whisper's `-l` taken from that language (ja, es, fr). Keep the existing
   uncaptioned-clip rule, generalised: a hero's uncaptioned non-`emote/`
   clips are in scope when that hero has any "Speaks …" clip, and they take
   that hero's language. The model id stays as it is: re-running Yamato
   must find 0 pending.
2. **Rename the view** from `data/vo/japanese.tsv` to `data/vo/foreign.tsv`,
   because it now holds three languages. Add a `lang` column. Update its
   `.do`, `all.do`, the repo `CLAUDE.md` clause, and the design doc's
   Layout row and Scope paragraph. Use `git mv` for the committed file.
3. **Run** `tengu`, `ghost` and `bebop` (whatever ledger names the hero
   keys produce), under the CPU rule.
4. **Fix up** the new rows in `transcripts/fixups.tsv` following 006's
   conventions: a replacement styled for a native reader of the language,
   an English translation, `doubt` when unsure, and escalation to turbo for
   doubtful clips. Ivy is a gargoyle; check her English captions in
   `lines.tsv` for context and tone. Quote all the new rows in your Final
   report: there are only about 36.

**Scope (only these files):** the `vo_asr*.py` modules and their tests,
`data/vo/japanese.tsv` → `data/vo/foreign.tsv` and its `.do`, `all.do`,
`bin/asr-start`, `transcripts/asr/*.tsv` (new heroes only),
`transcripts/fixups.tsv` (new rows only), the repo `CLAUDE.md` clause,
the Layout and Scope parts of
`docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md`, this
file.

## Steps

## Decisions

## Open Questions

## Final report
