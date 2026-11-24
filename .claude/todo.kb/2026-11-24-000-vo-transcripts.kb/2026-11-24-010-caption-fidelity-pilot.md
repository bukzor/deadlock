---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.kb/2026-11-24-008-other-languages.md
required-reading:
  - .claude/todo.kb/2026-11-24-000-vo-transcripts.kb/CLAUDE.md
  - docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md
  - docs/dev/environment.kb/whisper-asr.md
  - docs/dev/formats.kb/vo-captions.md
  - src/bukzor_deadlock/vo_asr*.py (as unit 008 left them)
  - data/vo/lines.tsv
---

# `caption fidelity pilot`: how often does Vyper's audio match her caption?

**Parent:** <https:../2026-11-24-000-vo-transcripts.md> (wave 8)

## Problem Statement

The owner has a theory: much of the English VO was ad-libbed or redirected
at the session, so what players hear often differs from the English
caption. They guess that 50 to 90% of Vyper's (`viper`) lines differ. A
mismatch list would be an accessibility bug report with evidence, possibly
the most useful thing to hand Valve. Pilot it on Vyper alone, and measure
before building anything permanent.

1. **ASR:** add an English mode to the job: in scope are a hero's clips
   with a real English caption, decoded with `-l en`, under the same
   ledger, batching and CPU rule. Run `viper`; her ledger is
   `transcripts/asr/viper.tsv`.
2. **Compare:** score each clip's ASR text against its caption after
   normalising case, punctuation and whitespace (word-level similarity of
   your choice; say which). Report the distribution.
3. **Judge:** for every clip below your similarity threshold, decide which
   of these it is:
   - an ASR error (the audio matches the caption);
   - a minor wording difference (same meaning, e.g. a dropped "the");
   - a material difference (different words or meaning: an ad-lib, a
     changed line, an extra sentence);
   - a different line entirely (the caption belongs to another take).

   Listening isn't possible, so when ASR quality is the question, rerun
   that clip on turbo f16 before judging. If clips judged as ASR errors
   cluster, tune the threshold.
4. **Report:**
   - the counts per class, and the rate of material or different-line
     clips out of all captioned clips;
   - 10 quoted examples of the material ones (caption against heard);
   - your estimate of the false-positive rate.

   Put the durable finding (method, rate, caveats) in a
   "Caption fidelity" section of `docs/dev/formats.kb/vo-captions.md`. Keep
   the per-clip judgments in `trash/vo-transcripts/010/`; don't commit a
   judgment ledger yet, since whether one is worth having is what this
   pilot decides.

**Scope (only these files):** `src/bukzor_deadlock/vo_asr*.py` (+ tests,
English mode only), `bin/asr-start` (if the mode needs a flag),
`transcripts/asr/viper.tsv`, the "Caption fidelity" section of
`docs/dev/formats.kb/vo-captions.md`, this file. Scratch:
`trash/vo-transcripts/010/`.

## Steps

## Decisions

## Open Questions

## Final report
