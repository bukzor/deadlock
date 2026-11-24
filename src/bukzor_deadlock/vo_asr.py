"""CLI: whisper transcripts of one hero's VO clips, into its ledger.

    python -m bukzor_deadlock.vo_asr [--english] HERO MODEL [CRC32 ...]

The scope is the hero's foreign-language clips (``vo_asr_ledger.clips``) or,
with ``--english``, its clips with a real English caption
(``vo_asr_ledger.captioned``), to check the audio against the caption. The
ledger keeps both scopes' rows whichever runs.
Whisper is pinned to each clip's language (``Clip.lang``), or detects it,
once per clip, under a model id that says so (``vo_asr_ledger.decoded_id``).
Without CRC32s, it transcribes every clip in scope
that has no row for MODEL (a ``MODELS`` key) yet, in batches of one language
(``vo_asr_batch.pack_languages``) on four one-thread processes; a clip that
comes back empty is rerun alone.
With CRC32s, it reruns each named clip alone, in one four-thread process,
replacing that model's row: the escalation of doubtful clips to a stronger
model.

It renices itself to 19 and uses 4 threads, the whole CPU budget the owner
leaves to background work. After each batch or clip it rewrites
``transcripts/asr/<hero>.tsv`` (``vo_asr_ledger``) through a temp file and a
rename, so a kill loses only the work in flight and a rerun resumes. It
never commits.

Inputs, built by redo beforehand (``bin/asr-start`` does it):
``data/vo/lines.tsv``, ``data/vo/audio/<hero>.d/`` and the model under
``data/tools/whisper/``. Progress goes to stderr.
"""

import os
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple

from . import paths
from .vo_asr_batch import decode_pcm, pack_languages, seconds, transcribe
from .vo_asr_ledger import AUTO, Clip, Row, captioned, clips, decoded_id, merge
from .vo_asr_ledger import parse, pending, render

VO = "sounds/vo/"
THREADS = 4


class Model(NamedTuple):
    id: str
    """The ledger's ``model`` cell: names the decode flags too, since they change the text."""
    file: str
    flags: tuple[str, ...]


MODELS = {
    "small": Model(
        "small/dtw/greedy",
        "ggml-small.bin",
        ("-dtw", "small", "-nfa", "-bs", "1", "-bo", "1"),
    ),
    "turbo": Model("large-v3-turbo/beam5", "ggml-large-v3-turbo.bin", ()),
}
"""Weakest first: ``vo_asr_view`` prefers the later model's row."""


def audio_file(audio_dir: Path, vsnd: str) -> Path:
    """Where ``data/vo/audio/`` holds the MP3 of the clip an event names.

    >>> audio_file(Path("audio"), "sounds/vo/yamato/ping/a.vsnd")
    PosixPath('audio/yamato.d/ping/a.mp3')
    """
    assert vsnd.startswith(VO) and vsnd.endswith(".vsnd"), vsnd
    hero_dir, rest = vsnd.removeprefix(VO).split("/", 1)
    return audio_dir / f"{hero_dir}.d" / f"{rest.removesuffix('.vsnd')}.mp3"


def load_lines(path: Path) -> list[dict[str, str]]:
    header, *lines = path.read_text().splitlines()
    names = header.split("\t")
    return [dict(zip(names, line.split("\t"), strict=True)) for line in lines]


@dataclass
class Ledger:
    """One hero's ledger file and its rows, saved after every change."""

    path: Path
    wanted: Sequence[Clip]
    rows: list[Row]

    def save(self, new: Sequence[Row]) -> None:
        self.rows = merge(self.rows, new, self.wanted)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.tmp")
        _ = tmp.write_text(render(self.rows))
        os.replace(tmp, self.path)


def model_file(model: Model) -> Path:
    return paths.data_dir() / "tools/whisper" / model.file


def clip_audio(clip: Clip) -> bytes:
    return decode_pcm(audio_file(paths.data_dir() / "vo/audio", clip.vsnd))


def transcribe_batch(
    model: Model, batch: Sequence[Clip], pcms: Sequence[bytes]
) -> list[Row]:
    """One process of one thread; an empty clip is rerun alone."""
    [lang] = {clip.lang for clip in batch}
    args = (model_file(model), model.flags, lang)
    texts = transcribe(*args, pcms, threads=1)
    if len(batch) > 1:
        texts = [
            text or transcribe(*args, [pcm], threads=1)[0]
            for text, pcm in zip(texts, pcms)
        ]
    model_id = decoded_id(model.id, lang)
    return [
        Row(clip.crc32, clip.vsnd, model_id, text) for clip, text in zip(batch, texts)
    ]


def run_batches(model: Model, todo: Sequence[Clip], ledger: Ledger) -> None:
    with ThreadPoolExecutor(THREADS) as pool:
        pcms = list(pool.map(clip_audio, todo))
        batches = pack_languages(
            [clip.lang for clip in todo], [seconds(pcm) for pcm in pcms], alone=AUTO
        )
        print(f"{len(todo)} clips in {len(batches)} batches", file=sys.stderr)
        futures = [
            pool.submit(
                transcribe_batch,
                model,
                [todo[i] for i in batch],
                [pcms[i] for i in batch],
            )
            for batch in batches
        ]
        done, t0 = 0, time.monotonic()
        for future in as_completed(futures):
            rows = future.result()
            ledger.save(rows)
            done += len(rows)
            print(
                f"{done}/{len(todo)} clips, {time.monotonic() - t0:.0f} s",
                file=sys.stderr,
            )


def run_clips(model: Model, todo: Sequence[Clip], ledger: Ledger) -> None:
    for clip in todo:
        [text] = transcribe(
            model_file(model),
            model.flags,
            clip.lang,
            [clip_audio(clip)],
            threads=THREADS,
        )
        model_id = decoded_id(model.id, clip.lang)
        ledger.save([Row(clip.crc32, clip.vsnd, model_id, text)])
        print(f"{clip.crc32}\t{clip.vsnd}\t{text}", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    args = (sys.argv if argv is None else argv)[1:]
    english = args[:1] == ["--english"]
    hero, model_name, *named = args[english:]
    model = MODELS[model_name]
    _ = os.nice(19)
    lines = load_lines(paths.data_dir() / "vo/lines.tsv")
    foreign, spoken_english = clips(lines, hero), captioned(lines, hero)
    wanted = spoken_english if english else foreign
    path = paths.repo_root() / "transcripts/asr" / f"{hero}.tsv"
    rows = parse(path.read_text()) if path.exists() else []
    ledger = Ledger(path, [*foreign, *spoken_english], rows)
    ledger.save([])
    if named:
        by_crc = {clip.crc32: clip for clip in wanted}
        missing = [crc32 for crc32 in named if crc32 not in by_crc]
        assert not missing, ("not in scope", missing)
        run_clips(model, [by_crc[crc32] for crc32 in named], ledger)
    else:
        run_batches(model, pending(wanted, ledger.rows, model.id), ledger)


if __name__ == "__main__":
    main()
