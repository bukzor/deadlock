"""Run whisper-cli once per clip and print one TSV row per clip.

    python docs/dev/probes/asr-bench.py MODEL CLIPDIR LISTFILE [WHISPER_ARG...]

LISTFILE holds clip paths relative to CLIPDIR, one per line. Extra args go to
``whisper-cli`` verbatim (e.g. ``-dl``, ``-l ja``, ``-ac 512``,
``--prompt ...``); ``-t`` defaults to 4. Columns: clip, detected lang, p,
encode ms, wall s, text. Run under ``nice -n 19`` to mimic the background job.
"""

import re
import subprocess
import sys
import time
from pathlib import Path

LANG = re.compile(r"auto-detected language: (\w+) \(p = ([\d.]+)\)")
ENCODE = re.compile(r"encode time =\s+([\d.]+) ms")
STAMP = re.compile(r"^\[[\d:.]+ --> [\d:.]+\]\s*", re.M)


def run(model: str, clip: Path, extra: list[str]) -> list[str]:
    args = ["whisper-cli", "-m", model, *extra, "-f", str(clip)]
    if "-t" not in extra:
        args[1:1] = ["-t", "4"]
    start = time.monotonic()
    proc = subprocess.run(args, capture_output=True, text=True, check=True)
    wall = time.monotonic() - start
    lang = LANG.search(proc.stderr)
    enc = ENCODE.search(proc.stderr)
    text = " ".join(STAMP.sub("", proc.stdout).split())
    return [
        clip.stem,
        lang.group(1) if lang else "",
        lang.group(2) if lang else "",
        enc.group(1) if enc else "",
        f"{wall:.1f}",
        text,
    ]


def main(model: str, clipdir: str, listfile: str, extra: list[str]) -> None:
    for line in Path(listfile).read_text().split():
        print("\t".join(run(model, Path(clipdir) / line, extra)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
