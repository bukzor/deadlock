# whisper.cpp ASR on this host

Measured 2026-11-24 with brew `whisper.cpp` 1.9.6 (`whisper-cli`) on the CPU
(Ryzen 5 3600, 6 cores / 12 threads, 7 GiB RAM, no GPU in WSL), every run
under `nice -n 19`. Input: Yamato VO clips, MP3 44.1 kHz mono, mean 1.6 s.
Models are the GGML files from `huggingface.co/ggerganov/whisper.cpp`.

## Tool behaviour

- `whisper-cli` reads MP3 directly. ffmpeg is needed only to concatenate
  clips for batching.
- brew's `whisper-cli` is an OpenMP build, and `-t N` alone doesn't bound
  its threads. At `-t 4`, one clip ran about 12 threads (4.7 s wall,
  32.6 s user). With `OMP_NUM_THREADS=4` it took 3.0 s wall and 10.2 s
  user. At `-t 1`, user time equals wall time either way. So set
  `OMP_NUM_THREADS` to the `-t` value, as `vo_asr_batch.transcribe` does.
- The default language is `en`. `-l ja` pins Japanese. Under `-l ja`,
  large-v3-turbo f16 still writes English speech as English. `small` and
  `medium` write it as katakana ("ラッシュダウンデル!" for "Lash, down
  there!"), and `base` drops it entirely.
- The encoder always runs a full 30 s window (`n_audio_ctx = 1500`), so a
  1 s clip costs as much encoding as 30 s of audio. That is why batching
  pays.
- `-ac N` (shorter audio context): `-dl` ignores it (same `p`, same time).
  On transcription, `-ac 128` cut turbo's encode from 13.4 s to 3.0 s, but
  the output degenerated into a repeated, misheard phrase and total time
  went up. Don't use it.
- `-dl` costs one full encode (about 13 s at 4 threads for turbo) and
  prints `auto-detected language: xx (p = ...)` on stderr.
- `-dtw <preset>` fills each token's `t_dtw` (10 ms units, in `-ojf`
  output) only together with `-nfa`. With flash attention on (the default),
  every `t_dtw` is silently −1.
- `-ojf` token texts are UTF-8 byte fragments (one kanji can span two
  tokens), so the JSON file isn't valid UTF-8. Read it with
  `errors="surrogateescape"` and join the tokens as bytes.
- `-ml 1 -sow` doesn't split Japanese, because `-sow` splits on spaces.

## Batching: many clips per encoder window

Concatenate clips with 1 s of silence after each, keeping the batch under
30 s (one window), then assign the output back to clips by time
([asr-batch]).

- **By segment**, only turbo f16 splits reliably: it gave one segment per
  clip on 53 of 53 spoken clips, across a window boundary too. A batch
  mostly of grunts still had 2 segments spanning a gap. turbo `q5_0`,
  `medium` `q5_0`, `small` and `base` merge neighbouring clips into one
  segment. turbo `q8_0` and large-v3 `q5_0` didn't merge on the one batch
  tried.
- **By token start**, the start offsets run 0.5 to 1 s late, so a clip's
  last token or two spills into the next clip.
- **By DTW time** (`-dtw small -nfa`), `small` put every word in the right
  clip on 56 clips. Only punctuation lands late, so punctuation stays with
  the token before it. 2 to 3 s gaps instead of 1 s didn't fix the
  segment-level drift, and they lost the English clips.
- A katakana `--prompt` of hero and ability names ([asr-prompt-ja]) drops
  all punctuation and makes segments contiguous (each segment starts where
  the last ended), which breaks segment mapping. It gained nothing:
  「OSIC」 was already right, since it's a lore organisation that the
  English VO captions also name.
- `emote/` grunts come out as 「はっ」 or nothing.

## Models: Japanese at `-l ja`

One batch of 8 Japanese clips (25 s) plus one of 4 clips (13 s: 1 Japanese,
3 English), 4 threads, quiet machine:

| model | file | wall (8 clips) | encode | Japanese | English clips |
|---|---|---|---|---|---|
| large-v3-turbo f16 | 1.6 GB | 15.6 s | 11.5 s | best | English text |
| large-v3-turbo `q5_0` | 574 MB | 15.2 s | 11.8 s | same as f16 | mixed |
| `medium` `q5_0` | 539 MB | 15.4 s | 7.5 s | good | katakana |
| `small` | 488 MB | 6.8 s | 2.9 s | intelligible | katakana |
| `small` `-dtw small -nfa -bs 1 -bo 1` | | 7.7 s | 3.8 s | intelligible | English text |
| `base` | 148 MB | 2.8 s | 1.1 s | garbled | dropped |

- Quantization doesn't speed up encoding on this CPU: turbo `q5_0` takes
  as long as f16. The large-v3 `q5_0` decoder (32 layers) took 72 s for
  9 clips, against 42 s for turbo `q5_0` and `q8_0` on the same busy
  machine.
- `small`'s mistakes are homophones and kana for kanji (時期に for じきに,
  この方の for この刀, 追い漏れ for 老いぼれ). A reader with context can
  still recover the line. `base` loses words (要者 for 容赦) and English
  clips.
- Greedy decoding (`-bs 1 -bo 1`) cut `small`'s wall time by about 15%
  with no visible change in the Japanese, and it wrote the 3 English clips
  as English ("Careful, Geriko!", "Lushed down there.", "I see the
  nurse.").

## Throughput within a 4-thread budget

64 clips in 8-clip batches, `small -dtw small -nfa -bs 1 -bo 1`, with a
foreground `pytest` run during each layout ([asr-layout]):

| layout | clips/h | foreground pytest |
|---|---|---|
| 1 process × 4 threads | 3335 | 16.2 s |
| 2 × 2 | 3097 | 17.3 s |
| 4 × 1 | 7589 | 16.4 s |
| turbo f16, 4 × 1 | 1641 | 23.0 s |

- Threads scale badly: four 1-thread processes do 2.3 times the work of
  one 4-thread process.
- These layouts ran without `OMP_NUM_THREADS` (see Tool behaviour), so the
  1 × 4 row was probably oversubscribed and understates what 4 bounded
  threads can do. 2 × 2 wasn't checked. The 4 × 1 rows are unaffected.
- `pytest` takes 12.3 s on an idle machine. The load average was already
  about 6 from other sessions, so this run can't attribute load to the job.
- Four turbo processes hold four copies of a 1.6 GB model in 7 GiB of RAM.

## Keying results by VPK CRC32

The pak index CRC32 of a clip changes only when its bytes change. Between
the older `data/manifest.jsonl` and build 6864, 1266 of the 1295 Yamato
`vsnd_c` paths present in both kept their CRC, and the other 29 changed
size as well. Across all of `sounds/vo/`, 0 of 53 407 surviving paths
changed CRC while keeping their size, and no added path reused a removed
path's CRC and size, so renames don't carry audio over
([asr-crc-stability]).

## Superseded measurements

Language detection, from before every clip was pinned to `-l ja`
([asr-bench]): `base` `-dl` (2 s a clip) labelled 30 of 30
"Speaks Japanese" clips `ja` and 27 of 30 English-captioned clips `en`.
The 3 misses were short accented pings (`el`, `ja` at p 0.69, `tr`), and
turbo `-l auto` called them `en`, `en` and `az`.

[asr-batch]: ../probes/asr-batch.py
[asr-bench]: ../probes/asr-bench.py
[asr-crc-stability]: ../probes/asr-crc-stability.py
[asr-layout]: ../probes/asr-layout.sh
[asr-prompt-ja]: ../probes/asr-prompt-ja.py
