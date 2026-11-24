---
status: proposed
date: "2026-11-24"
---

# ML observations are committed ledgers, outside `data/`

> [!DRAFT] agent-authored 2026-11-24 (vo-transcripts coordinator), vetoable.
> Owner rulings it builds on are in
> `.claude/todo.kb/2026-11-24-000-vo-transcripts.md`, Problem Statement.

ASR transcripts and the texts written from them can't be rebuilt
deterministically: a rerun on another model, version or machine gives
different text. So they aren't build outputs. They are observations,
recorded once and committed, the way `packages/bukzor-deadlock-measurements`
records in-game readings. Redo reads them as inputs and never writes them.

## Scope

Only clips whose English caption in `data/vo/lines.tsv` is
"Speaks <language>": Yamato's 532 "Speaks Japanese", Ivy's (`tengu`) 34
"Speaks spanish", and one "Speaks French" each for Lady Geist (`ghost`) and
Bebop. Whisper is pinned to the caption's language. A hero with any such
clip also brings its uncaptioned clips outside `emote/` (Yamato 11, Ivy 14,
Lady Geist 33, Bebop 23: alternate takes and pings). Their language is
detected, under a model id ending `/auto`, except Yamato's: hers are
alternate takes of Japanese lines, pinned to `ja`. Lady Geist and Bebop
speak English with one French line each, and small pinned to `fr` or `es`
translates English speech instead of transcribing it. Clips with a real
caption are English, and the caption is almost always right (Vyper: 5 of
1717 differ materially; `formats.kb/vo-captions.md`, Caption fidelity).
The English mode (`vo_asr --english`, `-l en`) transcribes them only for
that check. Its rows share the hero's ledger, and no fix-up is written for
them. `emote/` holds only grunts. Each clip in scope gets two texts: a **replacement**, meaning accurate text in the
orthography a native reader of its language expects, and a
**translation**, meaning English that tells players what is meant.

## Layout

| path | what | written by | committed |
|---|---|---|---|
| `data/vo/lines.tsv` | `hero event vsnd crc32 english`, one row per clip | redo | yes |
| `data/vpk/citadel/sounds/vo.d/` | raw `vsnd_c` | redo (explode) | no |
| `data/vo/audio/<hero>.d/` | the MP3 inside each `vsnd_c` (VRF `-d`); also for listening | redo | no |
| `data/tools/whisper/<model>.bin` | the GGML model, fetched | redo | no |
| `transcripts/asr/<hero>.tsv` | `crc32 vsnd model text`, one row per clip and model | the ASR job | **yes** |
| `transcripts/fixups.tsv` | `asr_text replacement translation doubt by` | the fix-up pass and the owner | **yes** |
| `transcripts/caption-corrections.tsv` | `crc32 vsnd caption suggested doubt by`: English clips whose audio departs materially from a real caption | a judge pass and the owner's ear | **yes** |
| `data/vo/foreign.tsv` | `hero event vsnd lang replacement translation doubt source`: the file to read | redo (join) | yes |

## Why this shape

- **ASR is keyed by clip and model.** The key is the clip's `crc32` from
  `lines.tsv`. Unit 004 checked it against an older build: 1266 of 1295
  surviving Yamato clips kept their CRC, and every CRC change came with a
  size change. Pending clips are the in-scope CRCs that have no row for the
  current model. Rows whose CRC has left the table are dropped; git history
  keeps them. A doubtful clip escalated to a stronger model gains a second
  row instead of losing its first.
- **Fix-ups are keyed by ASR text.** A repeated line is fixed up once, and a
  re-ASR that yields the same text reuses the fix-up. The join prefers the
  strongest model's row that has a fix-up.
- **`doubt` marks what context can't settle,** such as a misheard loanword
  (「OSIC」). Only those clips are rerun on a stronger model, and whatever
  stays doubtful goes to the owner.
- **`by` records the authority:** a model id (`claude-opus-5.5`) or
  `@bukzor`. Agent passes fill blanks and may replace model-written rows,
  but never overwrite an `@bukzor` row.
- **Outside `data/`.** Everything under `data/` is a redo output
  (`generated-output-under-data-via-redo.md`). A ledger there would need
  `.gitignore` exceptions, and redo's ownership rules would fight a file
  that redo doesn't write.
- **One ASR file per hero.** That keeps diffs local, and jobs on different
  heroes can't collide.

## The ASR job runs slowly, in the background

- **Pinned:** `whisper-cli -l <caption's language>` with no detection pass
  and no prompt (detection only for the uncaptioned clips above). The
  bar is intelligible, not accurate (owner ruling), and the fix-up pass
  recovers the rest from context.
- **Model and batching:** `ggml-small.bin` with
  `-l <lang> -dtw small -nfa -bs 1 -bo 1`. A detected clip runs alone,
  since whisper detects once per window. Batches of about 10 clips stay
  under 30 s, with 1 s of silence after each clip. Each batch is decoded
  to PCM with ffmpeg and split back into clips by DTW token time, because
  small merges neighbouring clips into one segment. A clip that comes back
  empty is rerun on its own. The measurements are in
  `../environment.kb/whisper-asr.md`.
- **The model id names the decode flags too** (for example
  `small/dtw/greedy`), since the flags change the text. A clip's text also
  depends on its batch neighbours, which is acceptable at the intelligible
  bar.
- **Escalation:** doubtful clips are rerun alone on `large-v3-turbo` f16,
  one process at a time. That model gives cleaner Japanese but uses about
  1.6 GB of RAM per copy, too much to run 4 copies of on 7 GiB.
- **Footprint:** 4 processes × 1 thread under `nice -n 19`, about 7600
  clips/h, so Yamato takes about 5 minutes. That is the whole 4-thread
  budget, so the owner keeps the foreground.
- **Kill-safe:** after each clip or batch, it rewrites the hero's ledger
  sorted, through a temp file and a rename. Killing it loses at most the
  work in flight, and a rerun resumes. It never commits.
- **Detached:** `tmux new -d -s asr '<cmd>'` survives a closed terminal and
  a crashed Claude session. To watch it, `tmux attach -t asr` or
  `wc -l transcripts/asr/*.tsv`. To stop it, `tmux kill-session -t asr`.

The fix-up pass is separate and cheap. An agent works through the ASR rows
that have no fix-up, in batches, with the hero, event name and the English
captions of neighbouring events as context. The CPU job never calls an LLM.

## Alternatives weighed

- **ASR everything, detecting the language:** costs two encoder passes per
  clip on 3.4 times as many clips. The captions already identify every
  English clip.
- **Commit only the joined view:** the ledgers' text would then exist only
  in a redo output, which a rebuild without the ledger would wipe.
- **One ledger holding ASR and fix-up together:** a re-ASR would orphan the
  fix-up, and repeated lines would be fixed up twice.
- **A runit service** (`/etc/service`): needs root and outlives the job;
  tmux is enough for a run that ends.

## What would change this

A deterministic ASR cheap enough to rerun on every patch would make the
ASR ledger an ordinary redo output. The fix-ups stay a ledger either way,
because they hold judgment.
