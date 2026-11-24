---
managed-by: Skill(llm-subtask)
status: done
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
  Coordinator amendment after 011: a `ja` row whose replacement is all
  ASCII is English speech (Yamato's 9, e.g. 「Vermin.」), so it *does*
  get a `japanese` row. Unit 011 treats those rows as English.
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

- [x] Copy the 17 locale VO and hero-name files to scratch (66 MB, 1 s)
- [x] Prep per-locale work files: each translation with its replacement,
      spoken language, and the locale's official caption of any VO line
      whose English is identical
- [x] Fan out translators, 2 locales each, writing to scratch
- [x] Assemble, validate, write the ledger; Layout row; spot-check French
- [x] Commit

## Decisions

- **Skip by the language actually spoken, not foreign.tsv's `lang`.** A
  `ja` row whose replacement has no kana or kanji is English (「Careful,
  Calico!」), so it gets a `japanese` row: the parent plan gives
  mislabelled English lines a bracket in every other locale. `auto` rows
  are English except Ivy's 「Tal vez debería comprar…」 (Spanish). A
  translation is skipped in a locale only when every row carrying it is
  spoken in that locale's language. Result: 75 translations in all 16
  locales, 522 in 15, 33 without `spanish`/`latam`, 2 without `french`.
- **Official captions first.** Where a game VO line has the identical
  English (case and punctuation ignored), its caption in that locale was
  given to the translator and used verbatim (109 of 631 in French).
- **Fan-out:** 8 sub-agents (Opus), 2 locales each, from per-locale work
  files plus a nickname lookup helper, all in scratch.
- **Official captions are not verbatim when the speaker's gender differs.**
  They come from other heroes' lines, and some are masculine. Coordinator
  fixes: `polish` 223, 224, 441; `czech` 441; `ukrainian` 441 now use
  feminine forms. A regex scan of the Slavic locales and a check of the
  Romance "not ready" lines found no others.
- **"Idol" is the Urn** (the game's internal `help_with_idol` pings). The
  `koreana`, `thai`, `polish` and `spanish` rows for 「Idol's here!」 now
  use each locale's Urn caption.
- **Ability names** follow each locale's VO captions. Where they differ from
  `citadel_heroes_<locale>.txt` (`spanish`/`latam`/`brazilian` Flying
  Strike, `schinese` all three), the VO caption wins.

## Open Questions

- Who Yamato addresses in some lines is unclear, so the listener's gender is
  a guess in gendered locales (masculine by default; e.g. `czech`/`french`
  287, 292, 361, 391).
- Fathom's old name 「Slorks」 (90, 91) is Slork in `czech`, `latam`,
  `brazilian`, `spanish`, `polish`, `turkish`, `indonesian`, `ukrainian`;
  Fathom in `german`, `russian`, `koreana`, `thai`, each following that
  locale's captions or the English.

## Final report

- Ledger: `transcripts/locale-translations.tsv`, 9522 rows across 16
  locales (632 translations; `japanese` 110, `spanish`/`latam` 599,
  `french` 630). Every row has 4 fields, and there are no zero-width
  spaces. `by` is `claude-opus-5-5`. The Layout row is in
  `docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md`.
- The amendment (all-ASCII `ja` rows get `japanese`) was already met: the
  no-kana/kanji rule picks out exactly the same 9 rows.
- Spot-check: French, a sample of 32 rows against Lady Geist's and Yamato's
  existing French captions. The tone matches: `tu` to enemies, a space
  before `!`/`?`, `…`, terse lines kept terse.
- Interjections are identical to the English where the locale writes them
  that way (「Ha!」, 「Aah!」).
- Tokens: about 1.1M for the sub-agents plus about 0.15M for the
  coordinator, over the 1M aim. Each translator re-read its 2 work files.
  One locale per agent would have cost more.
- `pytest` and `pyright` pass. No code was added in `src/`. Scratch is in
  `trash/vo-transcripts/012/` (`prep.py`, `assemble.py`, `fixes.tsv`,
  `out/`).
