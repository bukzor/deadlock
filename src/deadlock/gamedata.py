"""Turn a decompiled KV3 game-data file into JSONL records.

    python -m deadlock.gamedata data/gamedata/scripts/heroes.vdata

Each top-level entry becomes one line: a mapping entry (e.g. a single hero) is
emitted as its fields plus a ``_key`` naming it; a scalar/list entry is emitted
as ``{"_key": ..., "_value": ...}``. This makes ``heroes.vdata`` one hero per
line, ``abilities.vdata`` one ability per line, etc. — grep/jq-friendly.
"""

import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

from . import jsonl, kv3
from .types import is_str_mapping


def records(
    root: Mapping[str, object], *, source: str | None = None
) -> Iterator[dict[str, object]]:
    """One record per top-level entry, keyed by its name under ``_key``.

    ``source`` (a file label) is added as ``_file`` so records from many files
    can be concatenated into one JSONL stream and still filtered by origin.
    """
    for key, value in root.items():
        jsonable = jsonl.to_jsonable(value)
        record: dict[str, object] = {}
        if source is not None:
            record["_file"] = source
        record["_key"] = key
        if is_str_mapping(jsonable):
            record.update(jsonable)
        else:
            record["_value"] = jsonable
        yield record


def main(argv: list[str]) -> None:
    for arg in argv[1:]:
        path = Path(arg)
        source = arg if len(argv) > 2 else None
        sys.stdout.write(jsonl.dump_lines(records(kv3.load(path), source=source)))


if __name__ == "__main__":
    main(sys.argv)
