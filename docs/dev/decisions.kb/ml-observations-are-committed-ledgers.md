---
status: proposed
date: "2026-11-24"
---

# ML observations are committed ledgers, outside `data/`

> [!DRAFT] agent-authored 2026-11-24 (vo-transcripts coordinator), vetoable.

ASR transcripts and their English renderings can't be rebuilt
deterministically: a rerun on another model, version or machine gives
different text, and a full pass takes hours of CPU. So they aren't build
outputs. They are observations, recorded once and committed, the way
`packages/bukzor-deadlock-measurements` records in-game readings. Redo reads
them as inputs and never writes them.

## Layout

| path | what | written by | committed |
|---|---|---|---|
| `data/vpk/citadel/sounds/vo.d/` | raw `vsnd_c` | redo (explode) | no |
| `data/vo-audio/<hero>.d/` | the MP3 inside each `vsnd_c` (VRF `-d`); also for listening | redo | no |
| `data/tools/whisper/<model>.bin` | the GGML model, fetched | redo | no |
| the per-soundbite table (unit 003) | event, audio path, audio CRC32, caption per locale | redo | yes |
| `transcripts/asr/<hero>.tsv` | `crc32 path model lang p text`, one row per clip and decode language | the population job | **yes** |
| `transcripts/english.tsv` | `lang text en by`: the English for a transcript text | translation passes and the owner | **yes** |
| `data/vo-english.tsv/<hero>.tsv` | event, path, English caption, `lang`, `en`, `source`: the file to read | redo (join) | yes |

whisper.cpp reads MP3 directly, so there are no WAV intermediates. Raw
whisper JSON isn't kept: the ledger row holds everything we use.

## Why this shape

- **Keyed so a patch reruns only what changed.** An ASR row is keyed by the
  clip's CRC32 from the VPK index (free, no decode). The population job
  computes pending as the table's CRCs minus the ledger's CRCs for the
  current model, and drops rows whose CRC left the table. Git history keeps
  them.
- **English is keyed by text, not clip.** A repeated line is translated
  once, and a re-ASR that yields the same text reuses the translation. The
  same table also corrects English mishearings (`en` `"Less down there."` →
  `"Lash, down there."`). The join takes `english.tsv`'s `en` when there is
  one, otherwise `text` if `lang` is `en`, otherwise blank (pending).
- **`by` records the authority.** It names a model id (`claude-opus-5.5`) or
  `@bukzor`. Agent passes fill blanks and may replace model rows, but never
  overwrite an `@bukzor` row.
- **Outside `data/`.** Everything under `data/` is a redo output
  (`generated-output-under-data-via-redo.md`). A ledger there would need
  `.gitignore` exceptions, and redo's ownership rules would fight a file
  that redo doesn't write.
- **Per-hero ASR files.** That keeps diffs local, and two population jobs on
  different heroes can't collide.

## Population runs slowly, in the background

`python -m bukzor_deadlock.asr <hero>...` (the name may change):

- **Per pending clip:** a `whisper-cli -dl` detection pass, then a transcribe
  pass with `-l <detected>` and a proper-noun `--prompt` in that language
  (hero and ability names). That costs the same two encoder passes as
  `-l auto`, and the prompt can't bias detection. When `p < 0.8`, it also
  decodes as the other language and writes both rows, and the translation
  pass picks the real one.
- **After each clip** it rewrites the hero's ledger sorted, through a temp
  file and a rename. Killing it at any moment loses at most the clip in
  flight, and a rerun resumes where it stopped. It never commits: the ledger
  is always consistent, so commit it whenever is convenient.
- **Footprint:** `nice -n 19`, `-t 4`. Measured 2026-11-24 on this Ryzen 5
  3600 (6 cores, 12 threads) with large-v3-turbo and `-ac 512`: a short clip
  takes about 20 s wall at 4 threads and about 19 s at 12. Threads past 4
  buy nothing, so 4 leaves 8 hardware threads free for the foreground. The
  two encoder passes are 93% of the time. Yamato's 1806 clips take about
  10 h, one overnight run. A quantized model (`q5_0`, `q8_0`) may halve
  that; measure before switching, since a new model id re-keys the ledger.
- **Detached:** `tmux new -d -s asr '<cmd>'` survives a closed terminal and a
  crashed Claude session. To watch it, `tmux attach -t asr`, or
  `wc -l transcripts/asr/*.tsv`. To stop it, `tmux kill-session -t asr`.

Translation is a separate, cheap pass. An agent reads the non-English rows
that have no `english.tsv` entry and translates them in batches with their
context (hero, event name). The CPU job never calls an LLM.

## Alternatives weighed

- **Commit only the joined view:** the ledgers' text would then exist only
  in a redo output, which a rebuild without the ledger would wipe.
- **One ledger with ASR and English together:** a re-ASR would orphan the
  translation, and repeated lines would be translated twice.
- **Ledgers under `data/` with `.gitignore` exceptions:** see Why.
- **A runit service** (`/etc/service`): needs root and outlives the job's
  purpose; tmux is enough for a run that ends.

## What would change this

A deterministic ASR (fixed model, single-threaded, bit-reproducible) cheap
enough to rerun on every patch would make the ledger an ordinary redo output.
