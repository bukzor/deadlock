"""Many clips in one whisper window, split back into one text per clip.

The encoder always runs a full 30 s window, so short clips are packed into
batches under 30 s with a second of silence after each, decoded as one, and
the output is assigned back to clips by token time. The method and its
measurements: ``docs/dev/environment.kb/whisper-asr.md`` and the probe it
cites, ``docs/dev/probes/asr-batch.py``.
"""

import json
import math
import os
import re
import subprocess
import tempfile
import wave
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict, cast

RATE = 16000
GAP = 1.0
PUNCT = re.compile(r"^[\s。、！？!?,.「」…]+$")

Token = TypedDict("Token", {"text": str, "t_dtw": int, "offsets": dict[str, int]})


class Segment(TypedDict):
    tokens: list[Token]


class Transcript(TypedDict):
    transcription: list[Segment]


def pack(
    durations: Sequence[float],
    *,
    window: float = 30.0,
    gap: float = GAP,
    most: int = 10,
) -> list[list[int]]:
    """Consecutive clips grouped so each batch, gaps included, fits the window
    and holds at most ``most`` clips; a clip too long for any window is alone."""
    batches: list[list[int]] = []
    length = math.inf
    for i, duration in enumerate(durations):
        if length + duration + gap > window or len(batches[-1]) >= most:
            batches.append([])
            length = 0.0
        batches[-1].append(i)
        length += duration + gap
    return batches


def cuts(durations: Sequence[float], *, gap: float = GAP) -> list[float]:
    """Each clip's slot end, in seconds: the middle of the gap after it, the last
    slot open-ended."""
    ends: list[float] = []
    t = 0.0
    for duration in durations:
        ends.append(t + duration + gap / 2)
        t += duration + gap
    ends[-1] = math.inf
    return ends


def split(doc: Transcript, slot_ends: Sequence[float]) -> list[str]:
    """One text per slot: each token goes to the slot holding its time (DTW
    time, else its start offset), except that punctuation, whose DTW time lands
    late, stays with the token before it. Token texts are UTF-8 fragments
    (surrogate-escaped), joined as bytes."""
    texts = [bytearray() for _ in slot_ends]
    i = -1
    for segment in doc["transcription"]:
        for tok in segment["tokens"]:
            if tok["text"].startswith("[_"):
                continue
            ms = tok["t_dtw"] * 10 if tok["t_dtw"] >= 0 else tok["offsets"]["from"]
            if i < 0 or not PUNCT.match(tok["text"]):
                i = next(i for i, end in enumerate(slot_ends) if ms / 1000 < end)
            texts[i] += tok["text"].encode("utf-8", errors="surrogateescape")
    return [text.decode(errors="replace").strip() for text in texts]


def decode_pcm(clip: Path) -> bytes:
    """The clip as 16 kHz mono s16le."""
    args = ["ffmpeg", "-loglevel", "error", "-threads", "1", "-i", str(clip)]
    args += ["-ar", str(RATE), "-ac", "1", "-f", "s16le", "-"]
    return subprocess.run(args, capture_output=True, check=True).stdout


def seconds(pcm: bytes) -> float:
    return len(pcm) / 2 / RATE


def transcribe(
    model: Path, flags: Sequence[str], pcms: Sequence[bytes], threads: int
) -> list[str]:
    """Run ``whisper-cli -l ja`` once over the clips, padded and concatenated;
    one text per clip.

    ``OMP_NUM_THREADS`` is pinned to ``threads``: brew's whisper-cli is an
    OpenMP build, and at ``-t 4`` it otherwise burns about 7 cores' worth of
    user time (one OpenMP thread per core), not 4."""
    env = {**os.environ, "OMP_NUM_THREADS": str(threads)}
    silence = bytes(2 * int(GAP * RATE))
    with tempfile.TemporaryDirectory(prefix="vo_asr.") as tmp:
        stem = Path(tmp) / "batch"
        with wave.open(f"{stem}.wav", "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(RATE)
            wav.writeframes(b"".join(pcm + silence for pcm in pcms))
        args = ["whisper-cli", "-m", str(model), "-t", str(threads), "-l", "ja", *flags]
        args += ["-np", "-ojf", "-of", str(stem), "-f", f"{stem}.wav"]
        _ = subprocess.run(args, capture_output=True, check=True, env=env)
        raw = Path(f"{stem}.json").read_text(encoding="utf-8", errors="surrogateescape")
    return split(
        cast(Transcript, json.loads(raw)), cuts([seconds(pcm) for pcm in pcms])
    )
