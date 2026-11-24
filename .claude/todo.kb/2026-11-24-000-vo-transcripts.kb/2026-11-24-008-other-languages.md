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
   clips are in scope when that hero has any "Speaks …" clip. The model id
   stays as it is: re-running Yamato must find 0 pending.
   **Amended mid-run (coordinator):** uncaptioned clips must not take the
   hero's foreign language. Lady Geist and Bebop speak English, with one
   French line each, so pinning their 33 and 23 uncaptioned clips to `fr`
   was the coordinator's error. For tengu, ghost and bebop, decode
   uncaptioned clips with whisper's language detection (`-l auto`, or `-dl`
   followed by `-l <detected>`). Use a model id that says so, so the
   French- and Spanish-pinned rows for those clips are superseded rather
   than mixed in; drop the superseded rows from the ledger. Yamato's
   uncaptioned rows stay as they are (pinned `ja`, already fixed up). Their
   fix-ups follow the same rules: an English clip's replacement is the
   English as heard, and its translation repeats it. These clips have no
   caption today, so the suggested text is useful in its own right.
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

- [x] Scope and `-l` from the caption (`vo_asr_ledger`, `vo_asr_batch`, `vo_asr`); tests
- [x] View renamed to `data/vo/foreign.tsv` with `lang`; `.do`, `all.do`, `CLAUDE.md`, design doc
- [x] ASR runs: tengu 48, ghost 34, bebop 24 clips on small; Yamato 0 pending
- [~] Fix-ups for the new rows; escalate doubtful to turbo
- [ ] Rebuild view; pytest, pyright; commit

## Decisions

- **`Clip` carries `lang`;** a hero speaks one language (asserted), so a
  batch has one `-l`. The caption must match "Speaks <language>" whole:
  atlas's "Uhhhh <speaks japanese>" stays out.
- **Every uncaptioned clip is escalated to turbo.** The generalised rule
  pulls in 70 uncaptioned clips (Ivy 14, Lady Geist 33, Bebop 23), almost
  all English pings and alt takes. small under `-l fr`/`-l es` *translates*
  English ("On va enlever Calico !"); turbo writes it as English ("Let's
  take out Calico."), as it did under `-l ja`. So turbo is the fix-up's
  source for them, and the replacement is the English spoken.

## Open Questions

## Final report
