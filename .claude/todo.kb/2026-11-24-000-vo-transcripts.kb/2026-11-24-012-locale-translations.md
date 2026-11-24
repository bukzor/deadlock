---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.md (Problem Statement)
  - docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md
  - data/vo/foreign.tsv
---

# `locale translations`: the bracketed translation in every locale

**Parent:** <https:../2026-11-24-000-vo-transcripts.md> (wave 9)

## Problem Statement

The caption mod (unit 011) shows each foreign line as the spoken text plus
a bracketed translation in the player's language. Today only the English
exists. Write the rest as a committed ledger,
`transcripts/locale-translations.tsv`, with columns
`translation locale text by`:
- `translation`: foreign.tsv's English `translation`, verbatim. This is
  the key, so a changed English translation leaves its old rows orphaned,
  not wrong.
- `locale`: the game's locale name (`french`, `schinese`, `latam`, …).
  Cover the 16 real non-English locales (every
  `citadel_generated_vo_<locale>.txt` over 1 KB), skipping a row's own
  spoken language (no Japanese for ja, no `spanish`/`latam` for es, no
  `french` for fr). Those captions drop the bracket.
- `text`: the translation, as that locale's own captions would phrase it.
  Translate from the spoken `replacement`, with the English for reference.
  Hero names and nicknames as that locale's VO captions render them; look
  them up in the game's `citadel_generated_vo_<locale>.txt` and
  `citadel_gc_hero_names_<locale>.txt` (read in place, never write under
  `$DEADLOCK_HOME`). Match the register (a curse stays a curse).
- `by`: your model id.

The table is one row per distinct (translation, locale), sorted by
translation then locale, UTF-8, no quoting, and no tab or newline in a
field. These are machine translations, and the mod's README will say so.
Spot-check one locale you read well against a sample of its existing
captions for tone, and say which in the Final report. Batch the work so
tokens go into translating, not re-reading; aim under 1M tokens.

Add the ledger's row to the Layout table in
`docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md`.

**Scope (only these files):** `transcripts/locale-translations.tsv`, that
one Layout row, this file. Scratch: `trash/vo-transcripts/012/`. No code
in `src/`. Unit 011 reads the ledger and runs in parallel.

## Steps

## Decisions

## Open Questions

## Final report
