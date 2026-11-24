"""Survey Yamato `vsnd*` manifest paths and the decompiled `.vsnd` text of her VO.

Usage: vsnd-survey.py MANIFEST BULK_DIR
  MANIFEST  data/manifest.jsonl
  BULK_DIR  output of `Source2Viewer-CLI -i pak01_dir.vpk -f sounds/vo/yamato/
            -e vsnd_c -o BULK_DIR -d` (one `.vsnd` KV3 text + `.mp3` per clip)

Prints: manifest split (own VO / other), then over the decompiled own-VO clips
the codec/rate/channel histogram, non-empty `m_Sentences` count, and total
duration (`m_flDuration`, header only).
"""

import collections
import json
import re
import sys
from pathlib import Path


def main(manifest: str, bulk: str) -> None:
    paths = [json.loads(line)["path"] for line in open(manifest)]
    ys = [p for p in paths if "yamato" in p.lower() and "vsnd" in p]
    own = [p for p in ys if p.startswith("sounds/vo/yamato/")]
    other_vo = [p for p in ys if p.startswith("sounds/vo/") and p not in set(own)]
    print(
        f"yamato vsnd paths: {len(ys)}; own VO {len(own)}; other heroes' VO {len(other_vo)}; non-VO {len(ys) - len(own) - len(other_vo)}"
    )
    sub = collections.Counter(
        p.split("/")[3] if p.count("/") > 3 else "(root)" for p in own
    )
    print("own VO by subdir:", dict(sub))
    fmt: collections.Counter[tuple[str, str, str]] = collections.Counter()
    sent = total = 0.0
    n = 0
    durs = []
    for f in Path(bulk).rglob("*.vsnd"):
        t = f.read_text()
        g = lambda k: re.search(rf"{k} = (.*)", t).group(1).strip('"')  # noqa: E731
        fmt[(g("m_nFormat"), g("m_nRate"), g("m_nChannels"))] += 1
        if not re.search(r"m_Sentences = \[\s*\]", t):
            sent += 1
        d = float(g("m_flDuration"))
        durs.append(d)
        total += d
        n += 1
    print("format/rate/channels:", dict(fmt))
    print(f"clips {n}; non-empty m_Sentences {int(sent)}")
    durs.sort()
    print(
        f"total {total:.0f}s = {total/60:.1f} min; mean {total/n:.2f}s; median {durs[n//2]:.2f}s; max {durs[-1]:.1f}s"
    )


main(*sys.argv[1:3])
