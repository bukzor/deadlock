"""The game build's identity, parsed from the install's ``steam.inf``.

With the raw extracts kept local, the committed views need provenance: which
build produced them. ``steam.inf`` carries the build's version/revision/date as
``Key=Value`` lines; this renders them as one-key-per-line JSON, so a patch bump
shows up as exactly the fields that changed.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

import typed_json


# Ordinals: sorting and subtracting these is meaningful ("how many revisions
# apart are these builds"). The appIDs are int-shaped but opaque handles —
# arithmetic on them means nothing — so they stay strings, as does everything
# else. Semantics decide this, not the shape of the value.
ORDINAL = frozenset({"ClientVersion", "ServerVersion", "SourceRevision"})


def fields(lines: Iterable[str]) -> dict[str, str | int]:
    """Parse ``steam.inf``-style ``Key=Value`` lines, ORDINAL keys as ints.

    >>> fields(["ClientVersion=6684\\n", "appID=1422450\\n"])
    {'ClientVersion': 6684, 'appID': '1422450'}
    """
    result: dict[str, str | int] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        key, sep, value = line.partition("=")
        assert sep, line
        result[key] = int(value) if key in ORDINAL else value
    return result


def render(fields: dict[str, str | int]) -> str:
    """Render fields as key-sorted, one-key-per-line JSON (newline-terminated).

    >>> print(render({"b": "2", "a": 1}), end="")
    {
      "a": 1,
      "b": "2"
    }
    """
    return typed_json.dumps(dict(sorted(fields.items())), indent=2) + "\n"


def main() -> None:
    _ = sys.stdout.write(render(fields(sys.stdin)))


if __name__ == "__main__":
    main()
