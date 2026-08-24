"""redo-adopt: mark existing files as redo-generated targets.

redo deliberately refuses to overwrite a file it didn't generate — djb's rule,
so a `default.c.do` can't clobber a hand-written `hello.c`. But it decides
"didn't generate" from its own state database, which a fresh `git clone`
doesn't have. So a *committed* build output looks hand-written, and redo skips
it while exiting 0: the build silently keeps stale content.

Adopting a target says "this file is mine, rebuild it when its dependencies
change" — the missing counterpart to redo's implicit disown.

After `redo-adopt PATH`:

- a target redo already owns and that nobody has touched is left alone — no
  rebuild is forced, so adopting repeatedly is free;
- in all other cases, including a PATH that doesn't exist yet, a subsequent
  redo will rebuild the target.

Usage: redo-adopt <path>...
"""

import importlib
import os
import shutil
import sys
from typing import Protocol, cast


class RedoFile(Protocol):
    """The slice of ``redo.state.File`` this depends on."""

    is_generated: bool
    is_override: bool
    changed_runid: int | None
    failed_runid: int | None
    stamp: str | None

    def read_stamp(self) -> str: ...
    def save(self) -> None: ...


class RedoState(Protocol):
    """The slice of ``redo.state`` this depends on — the whole untyped surface."""

    def init(self, targets: list[str]) -> None: ...
    def File(self, name: str) -> RedoFile: ...  # noqa: N802  (redo's own name)
    def commit(self) -> None: ...


def _redo_state() -> RedoState:
    """Import redo's state module, which lives in a private lib dir beside its
    executables and ships no stubs; the Protocols above are the typed boundary."""
    exe = shutil.which("redo")
    if not exe:
        sys.exit("redo-adopt: redo is not on PATH")
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(exe)), "..", "lib"))
    return cast(RedoState, cast(object, importlib.import_module("redo.state")))


def adopt(paths: list[str]) -> None:
    state = _redo_state()
    state.init([])
    for path in paths:
        if not os.path.exists(path):
            continue  # nothing owns it, so redo will build it: already adopted
        f = state.File(name=os.path.abspath(path))
        if f.is_generated and not f.is_override and f.stamp == f.read_stamp():
            continue  # already ours and untouched
        # Recording the current stamp keeps redo from reading this as a target
        # edited behind its back (which demotes it to a static file); the unset
        # changed_runid — "mine, never built" — is what makes redo rebuild it.
        f.stamp = f.read_stamp()
        f.is_generated = True
        f.is_override = False
        f.changed_runid = None
        f.failed_runid = None
        f.save()
    state.commit()


def main(argv: list[str] | None = None) -> None:
    paths = (sys.argv if argv is None else argv)[1:]
    if not paths:
        sys.exit("usage: redo-adopt <path>...")
    adopt(paths)


if __name__ == "__main__":
    main(sys.argv)
