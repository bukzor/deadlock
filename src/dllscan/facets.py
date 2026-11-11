"""Each facet's document, assembled from a loaded DLL: pure over `Memory` and
`Image`, so WSL pytest drives it with fakes. `__main__` is the only caller and
does the loading.

Output is deterministic: lists keep queue order (position is the index) or are
sorted, and nothing machine-specific (addresses, the install path) goes in.
"""

import json
import ntpath
from collections.abc import Iterable, Sequence

from .document import ConCommandsDocument, ConVarsDocument, LoadFailed, LoadOk
from .alloclog import Alloc, locate
from .entries import decode_concommand, decode_convar
from .image import Image
from .memory import Memory
from .reglist import find_queues
from .shape import ShapeError
from .win32 import Win32Error

def load_ok(before: Iterable[str], after: Iterable[str]) -> LoadOk:
    """The modules a load added: `after - before`, sorted. Leaves out what
    Python itself holds, which changes with every Python upgrade."""
    return LoadOk(outcome="ok", modules=sorted(set(after) - set(before)))


def load_failed(error: Win32Error) -> LoadFailed:
    """The error as function and numeric code: no path (it varies by install)
    and no `FormatMessage` text (it varies by locale)."""
    return LoadFailed(outcome="failed", error=f"{error.function}: {error.code}")


def concommands(mem: Memory, image: Image, dll: str, log: Sequence[Alloc] | None) -> ConCommandsDocument:
    """The command queue of the image loaded from `dll` (a Windows path),
    decoded; empty if it has none. `log` is the allocations its load made
    (`alloclog.load`), None for tier0. The document's `dll` is the path's
    basename as given, case kept: the key into `data/dlls.list`."""
    entries = [decode_concommand(mem, entry, image) for entry in _queue(mem, image, "concommands", log)]
    return ConCommandsDocument(dll=ntpath.basename(dll), concommands=entries)


def convars(mem: Memory, image: Image, dll: str, log: Sequence[Alloc] | None) -> ConVarsDocument:
    """The convar queue, as `concommands` decodes the command queue."""
    entries = [decode_convar(mem, entry, image) for entry in _queue(mem, image, "convars", log)]
    return ConVarsDocument(dll=ntpath.basename(dll), convars=entries)


def _queue(mem: Memory, image: Image, kind: str, log: Sequence[Alloc] | None) -> tuple[int, ...]:
    """The entries of the image's `kind` queue, none if it has none: located
    from `log`, or for tier0 (no log: its queues predate any hook) by the
    shape scan, which must find at most one."""
    if log is not None:
        queue = locate(mem, image, kind, log)
        return queue.entries if queue else ()
    queues = find_queues(mem, image, kind)
    if len(queues) > 1:
        raise ShapeError(f"more than one {kind} queue", [hex(q.head) for q in queues])
    return queues[0].entries if queues else ()


def dumps(document: object) -> str:
    """`document` as UTF-8-ready JSON text: one value per line (a changed value
    diffs as one line), keys in the order the document types declare them,
    non-ASCII kept as is, and a final newline."""
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
