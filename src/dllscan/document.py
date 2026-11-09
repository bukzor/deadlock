"""The JSON documents of the per-DLL store, one ``TypedDict`` per facet.

One document is one facet of one DLL (``data/dlls/<facet>/<dll>.json``). The
scanner builds them on Windows and the ``deadlock.dlls_<facet>`` aggregators
read them on WSL; both import these types, so pyright checks the documents on
both sides of the process boundary.

Rules shared by every document (``docs/dev/cvar-dump.kb/output-views.md``):

- No addresses: ASLR moves them every run.
- No build stamp: the DLL's bytes already key the target.
- No queue index: a list is in queue order, so position is the index. A stored
  index would renumber every later entry when one is inserted early.
- Every key is always present. An absent value is ``null``, never a missing key,
  so every entry has the same shape and the same line count when pretty-printed:
  a value that appears shows as one changed line, not an inserted one, and the
  TSV aggregates get a fixed column set.

``module`` is the DLL's basename as listed in ``data/dlls.list``.
"""

from collections.abc import Sequence
from typing import Literal, TypedDict

type ConVarValue = bool | int | float | str | Sequence[float]
"""A ``CVValue_t`` decoded by its convar's ``type`` (``dllscan.values``).

``bool``, ``int`` (int8 … uint64), ``float`` (float32 as the shortest decimal
that reads back as the same float32; float64), ``str`` (string), or a list of
numbers (``color``: 4 ints r, g, b, a; vector2/3/4, qangle, vectorws: floats).
Every type decodes; bytes that don't fit theirs are a ``ShapeError``.
"""


class FileDocument(TypedDict):
    """The ``file`` facet: the DLL's bytes on disk."""

    size: int
    sha256: str  # lowercase hex


class LoadOk(TypedDict):
    """The DLL loaded; ``modules`` is the modules the load added to the process
    (the DLL and the part of its import closure not already loaded), as sorted
    basenames."""

    outcome: Literal["ok"]
    modules: Sequence[str]


class LoadFailed(TypedDict):
    """``LoadLibrary`` refused the DLL (e.g. a dependency isn't found)."""

    outcome: Literal["failed"]
    error: str


class LoadExcluded(TypedDict):
    """Never loaded (a load hangs and leaves an unkillable process); written
    WSL-side from the exclusion list."""

    outcome: Literal["excluded"]
    reason: str


type LoadDocument = LoadOk | LoadFailed | LoadExcluded
"""The ``load`` facet, discriminated on ``outcome``."""


class ConVar(TypedDict):
    """One convar declaration, as its reg-list queue entry records it.

    ``flags``: FCVAR names, unknown bits as ``flag_<n>``. ``type``: the
    binary's ``EConVarType`` name. ``version``: the declaration's
    ``m_Version`` (nonzero on a few ``archive`` convars).
    ``default``/``min``/``max`` are ``null`` when the declaration's has-default
    / has-min / has-max byte is 0 (has-default is 0 on a ``reference``
    declaration).
    """

    name: str
    help: str | None
    flags: Sequence[str]
    type: str
    version: int
    default: ConVarValue | None
    min: ConVarValue | None
    max: ConVarValue | None


class ConVarsDocument(TypedDict):
    """The ``convars`` facet: one DLL's convar queue, in queue order,
    duplicates kept."""

    module: str
    convars: Sequence[ConVar]


class ConCommand(TypedDict):
    """One concommand declaration, as its reg-list queue entry records it."""

    name: str
    help: str | None
    flags: Sequence[str]


class ConCommandsDocument(TypedDict):
    """The ``concommands`` facet: one DLL's command queue, in queue order,
    duplicates kept."""

    module: str
    concommands: Sequence[ConCommand]
