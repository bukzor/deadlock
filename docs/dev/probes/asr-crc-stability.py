"""Did VPK CRC32s of VO clips survive patches where the clip didn't change?

    ./bin/shell python docs/dev/probes/asr-crc-stability.py [PREFIX]

Compares ``data/manifest.jsonl`` (an older build's index) against the live
``pak01_dir.vpk`` index for every ``vsnd_c`` under PREFIX (default
``sounds/vo/yamato/``), and prints counts by outcome.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import cast

from bukzor_deadlock import paths
from bukzor_deadlock.archive import read_entries


def main(prefix: str) -> None:
    old: dict[str, tuple[str, int]] = {}
    with Path("data/manifest.jsonl").open() as f:
        for line in f:
            rec = cast(dict[str, str | int], json.loads(line))
            path, crc, size = str(rec["path"]), str(rec["crc32"]), int(rec["size"])
            if path.startswith(prefix) and path.endswith(".vsnd_c"):
                old[path] = (crc, size)
    new = {
        e.path: (f"{e.crc32:08x}", e.file_length)
        for e in read_entries(paths.vpk_dir_file())
        if e.path.startswith(prefix) and e.path.endswith(".vsnd_c")
    }
    outcome: Counter[str] = Counter()
    for path in old.keys() | new.keys():
        if path not in new:
            outcome["removed"] += 1
        elif path not in old:
            outcome["added"] += 1
        elif old[path] == new[path]:
            outcome["same crc, same size"] += 1
        elif old[path][1] == new[path][1]:
            outcome["new crc, same size"] += 1
        else:
            outcome["new crc, new size"] += 1
    # A rename that kept the bytes: an added path whose (crc, size) was in old.
    old_keys = set(old.values())
    outcome["added, crc+size seen in old"] = sum(
        1 for p, v in new.items() if p not in old and v in old_keys
    )
    print(f"prefix={prefix} old={len(old)} new={len(new)}")
    for k, v in sorted(outcome.items()):
        print(f"{v:6d}  {k}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sounds/vo/yamato/")
