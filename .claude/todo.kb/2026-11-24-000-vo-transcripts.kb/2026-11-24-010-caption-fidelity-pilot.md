---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
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

- [x] English mode: `vo_asr_ledger.captioned` (tests first), `--english` in
  `vo_asr`, flag passthrough in `bin/asr-start`
- [x] Run `viper` small, English (`transcripts/asr/viper.tsv`): 1717 clips, 22 min
- [x] Compare: similarity per clip, distribution
- [x] Judge sub-threshold clips (24 turbo reruns)
- [x] Report: doc section, this file, commit

## Decisions

- **One ledger, both scopes.** Either mode merges against foreign ∪ English
  clips, so neither run drops the other's rows; `vo_asr_view` still keys
  on `clips()`, so `foreign.tsv` is unchanged (checked byte for byte).
- **Similarity:** difflib ratio over word lists. Normalising only case,
  punctuation and whitespace flagged every `Paige's`/`Paige is`, so
  contractions and spoken spellings are expanded on both sides too.
- **Threshold 1.0:** every imperfect clip judged (702). One material clip
  scored 0.91, and ASR errors cluster by clip type (pings), not score.
- **Minor vs material** by meaning, as captioning's clean-verbatim
  standard does: dropped fillers, openers, false starts and hedges
  ("You know what", "I gotta say") are minor; a new clause or changed
  referent is material.

## Open Questions

- `ml-observations-are-committed-ledgers.md` (Scope) still says the ledger
  holds only foreign clips; English-mode rows now exist. Not in my scope.
- Needs a listener: `5e5edcdc` (`can`/`can't`), and `4740d85a` "Took out
  Celeste.", heard "The guy's Celeste." by both models (judged ASR).
- A judgment ledger isn't worth committing at 5 of 1717. For other heroes,
  reading the non-ping clips and `*_killed_in_lane_*` nicknames would
  cover what matters; a hero-name `--prompt` for English mode might cut the
  ping noise, but that's untested.

## Final report

- Checks: `pytest` and `pyright` clean (whole repo).
- Findings: the "Caption fidelity" section of
  `docs/dev/formats.kb/vo-captions.md`. Counts: 1015 exact; of 702 judged,
  413 ASR, 284 minor, 5 material, 0 different take. The material or
  different-line rate is **0.3% (5/1717)**, against the owner's guess of
  50 to 90%. Any word differs in 17% of all clips and 33% of non-ping ones.
- Deviation: the brief asked for 10 material examples; only 5 exist (all
  quoted in the doc). For contrast, the largest minor ones: "Never cared
  for teachers." / "You know what, I've never cared for teachers."; "Hey
  the ritual's about to start, we can talk about this later." / "Hey, so,
  oh gosh, the ritual's about to start, so we're gonna have to talk about
  this later."; "Not New Jersey, Wisconsin - lots of assassins in
  Wisconsin." / "No, not New Jersey, Wisconsin. There's actually a lot of
  assassins in Wisconsin." (all turbo-confirmed).
- False positives: about 20% of material calls (1 of 5); near 0 for
  filler differences. Possible hidden misses put the rate at up to 0.6%.
- Scratch (`trash/vo-transcripts/010/`): `compare.py` (scorer),
  `scores.tsv`, `judgments.tsv` (per-clip class), `tally.py`, `turbo.log`.
