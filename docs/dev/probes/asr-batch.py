"""Transcribe several clips in one whisper window, then split back per clip.

    python docs/dev/probes/asr-batch.py MODEL CLIPDIR LISTFILE OUTSTEM [WHISPER_ARG...]

Decodes each clip in LISTFILE (paths relative to CLIPDIR) to 16 kHz mono,
appends GAP seconds of silence (env ``GAP``, default 1), concatenates them
into OUTSTEM.wav, and runs ``whisper-cli -ojf`` on it (``-t 4`` unless given).

Splitting is per token, not per segment: every model but large-v3-turbo f16
merges neighbouring clips into one segment. A token's time is its DTW time
when ``-dtw <model>`` was given, else its start offset; it belongs to the clip
whose slot holds that time, slots cut at the middle of each gap, except that
punctuation (whose DTW time lands late) stays with the token before it. Token texts
are byte fragments of UTF-8 (one kanji can span two tokens), so they are
joined as bytes per clip.

Prints one TSV row per clip (clip, slot, token count, text), then how many
clips got no text, and the run's wall and encode time.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

RATE = 16000
GAP = float(os.environ.get("GAP", "1.0"))
ENCODE = re.compile(rb"encode time =\s+([\d.]+) ms")
PUNCT = re.compile(r"^[\s。、！？!?,.「」…]+$")


Token = TypedDict("Token", {"text": str, "t_dtw": int, "offsets": dict[str, int]})


class Segment(TypedDict):
    tokens: list[Token]


class Transcript(TypedDict):
    transcription: list[Segment]


def pcm(clip: Path) -> bytes:
    args = ["ffmpeg", "-loglevel", "error", "-i", str(clip)]
    args += ["-ar", str(RATE), "-ac", "1", "-f", "s16le", "-"]
    return subprocess.run(args, capture_output=True, check=True).stdout


def concat(clips: list[Path], wav: Path) -> list[float]:
    """Write the padded concatenation; return each slot's end in seconds."""
    audio = bytearray()
    cuts: list[float] = []
    for clip in clips:
        audio += pcm(clip)
        cuts.append(len(audio) / 2 / RATE + GAP / 2)
        audio += bytes(2 * int(GAP * RATE))
    _ = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(RATE)]
        + ["-ac", "1", "-i", "-", str(wav)],
        input=bytes(audio),
        check=True,
    )
    cuts[-1] = float("inf")
    return cuts


def main(model: str, clipdir: str, listfile: str, stem: str, extra: list[str]) -> None:
    clips = [Path(clipdir) / line for line in Path(listfile).read_text().split()]
    wav = Path(f"{stem}.wav")
    cuts = concat(clips, wav)
    threads = [] if "-t" in extra else ["-t", "4"]
    args = [
        "whisper-cli",
        "-m",
        model,
        *threads,
        *extra,
        "-ojf",
        "-of",
        stem,
        "-f",
        str(wav),
    ]
    t0 = time.monotonic()
    proc = subprocess.run(args, capture_output=True, check=True)
    wall = time.monotonic() - t0
    raw = Path(f"{stem}.json").read_text(encoding="utf-8", errors="surrogateescape")
    texts = [bytearray() for _ in clips]
    counts = [0 for _ in clips]
    i = -1
    doc = cast(Transcript, json.loads(raw))
    for seg in doc["transcription"]:
        for tok in seg["tokens"]:
            if tok["text"].startswith("[_"):
                continue
            t = tok["t_dtw"] * 10 if tok["t_dtw"] >= 0 else tok["offsets"]["from"]
            if not PUNCT.match(tok["text"]) or i < 0:
                i = next(i for i, cut in enumerate(cuts) if t / 1000 < cut)
            texts[i] += tok["text"].encode("utf-8", errors="surrogateescape")
            counts[i] += 1
    start = 0.0
    for clip, cut, n, text in zip(clips, cuts, counts, texts):
        print(
            f"{clip.stem}\t{start:.2f}-{cut:.2f}\t{n}\t{text.decode(errors='replace').strip()}"
        )
        start = cut
    enc = ENCODE.search(proc.stderr)
    print(f"# {counts.count(0)} clips got no text")
    print(
        f"# {len(clips)} clips, wall {wall:.1f} s, encode {enc and enc.group(1).decode()} ms"
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
