"""Each facet's document, assembled from a loaded DLL: pure over `Memory` and
`Image`, so WSL pytest drives it with fakes. `__main__` is the only caller and
does the loading.

Output is deterministic: lists keep queue order (position is the index) or are
sorted, and nothing machine-specific (addresses, the install path) goes in.
"""

import json
import ntpath
from collections.abc import Iterable, Mapping
from typing import TypedDict

from .document import ConCommandsDocument, ConVarsDocument, LoadFailed, LoadOk
from .entries import decode_concommand, decode_convar, decode_creation_base
from .image import Image
from .memory import Memory
from .reglist import STRIDES, Queue, find_queues, learn_strides
from .shape import ShapeError
from .win32 import Win32Error

ANCHORS: Mapping[str, str] = {
    "bot_kick_all": "concommands",
    "citadel_bot_kick": "concommands",
    "find": "concommands",
    "citadel_lane_swap_available_duration_prematch": "convars",
}
"""Names known by other means to be in a queue of this kind
(`docs/dev/convar-dump.kb/validation.md`, "Anchors"). `find` is tier0's."""


class LearnedStride(TypedDict):
    """One queue `learn_strides` found: `kind` is the `STRIDES` key its
    anchors name, or None if it holds none."""

    stride: int
    kind: str | None
    entries: int


def load_ok(before: Iterable[str], after: Iterable[str]) -> LoadOk:
    """The modules a load added: `after - before`, sorted. Leaves out what
    Python itself holds, which changes with every Python upgrade."""
    return LoadOk(outcome="ok", modules=sorted(set(after) - set(before)))


def load_failed(error: Win32Error) -> LoadFailed:
    """The error as function and numeric code: no path (it varies by install)
    and no `FormatMessage` text (it varies by locale)."""
    return LoadFailed(outcome="failed", error=f"{error.function}: {error.code}")


def concommands(mem: Memory, image: Image, dll: str) -> ConCommandsDocument:
    """The command queue of the image loaded from `dll` (a Windows path),
    decoded; empty if it has none, `ShapeError` if it has two. `module` is
    `dll`'s basename as given, case kept: the key into `data/dlls.list`."""
    entries = [decode_concommand(mem, entry, image) for entry in _queue(mem, image, "concommands")]
    return ConCommandsDocument(module=ntpath.basename(dll), concommands=entries)


def convars(mem: Memory, image: Image, dll: str) -> ConVarsDocument:
    """The convar queue, as `concommands` decodes the command queue."""
    entries = [decode_convar(mem, entry, image) for entry in _queue(mem, image, "convars")]
    return ConVarsDocument(module=ntpath.basename(dll), convars=entries)


def _queue(mem: Memory, image: Image, kind: str) -> tuple[int, ...]:
    """The entries of the image's one `kind` queue; none if it has none."""
    queues = find_queues(mem, image, kind)
    if len(queues) > 1:
        raise ShapeError(f"more than one {kind} queue", [hex(q.head) for q in queues])
    return queues[0].entries if queues else ()


def strides(mem: Memory, image: Image) -> list[LearnedStride]:
    """The multi-block queues' strides, re-learned and labelled by `ANCHORS`.

    `ShapeError` unless they are exactly the pinned `STRIDES` and each labelled
    one has its kind's stride; an unlabelled queue only counts toward the first."""
    learned = [_label(mem, image, q) for q in learn_strides(mem, image)]
    found = sorted(s["stride"] for s in learned)
    if found != sorted(STRIDES.values()):
        raise ShapeError("strides moved", learned, STRIDES)
    for s in learned:
        if s["kind"] is not None and s["stride"] != STRIDES[s["kind"]]:
            raise ShapeError("anchor in the wrong queue", s, STRIDES)
    return learned


def _label(mem: Memory, image: Image, queue: Queue) -> LearnedStride:
    names = {decode_creation_base(mem, entry, image)["name"] for entry in queue.entries}
    kinds = {ANCHORS[name] for name in names & ANCHORS.keys()}
    if len(kinds) > 1:
        raise ShapeError("queue holds anchors of both kinds", hex(queue.head), sorted(names & ANCHORS.keys()))
    return LearnedStride(stride=queue.stride, kind=next(iter(kinds), None), entries=len(queue.entries))


def dumps(document: object) -> str:
    """`document` as UTF-8-ready JSON text: one value per line (a changed value
    diffs as one line), keys in the order the document types declare them,
    non-ASCII kept as is, and a final newline."""
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
