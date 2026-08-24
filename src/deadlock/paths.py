"""Where things live, resolved deterministically from the environment.

Every path the parsers touch comes from here so that runs are reproducible and
overridable in tests / CI without editing code. Defaults point at a stock
Windows Steam install seen through WSL (``/mnt/c``).

Environment overrides:
    DEADLOCK_GAME_DIR  the ``.../Deadlock/game`` directory
    DEADLOCK_DATA_DIR  where generated output is written (default ``<repo>/data``)
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

DEFAULT_GAME_DIR = Path(
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/Deadlock/game"
)


def _env(name: str, environ: dict[str, str] | None) -> str | None:
    return (environ if environ is not None else os.environ).get(name)


def game_dir(environ: dict[str, str] | None = None) -> Path:
    """The Deadlock ``game`` directory (contains ``citadel/`` and ``core/``)."""
    override = _env("DEADLOCK_GAME_DIR", environ)
    return Path(override) if override else DEFAULT_GAME_DIR


def citadel_dir(environ: dict[str, str] | None = None) -> Path:
    """The primary content mod directory holding ``pak01_dir.vpk``."""
    return game_dir(environ) / "citadel"


def vpk_dir_file(environ: dict[str, str] | None = None) -> Path:
    """The VPK directory file that indexes all ``pak01_NNN.vpk`` archives."""
    return citadel_dir(environ) / "pak01_dir.vpk"


def steam_inf(environ: dict[str, str] | None = None) -> Path:
    """The build-identity file (``ClientVersion``, ``SourceRevision``, date)."""
    return citadel_dir(environ) / "steam.inf"


def repo_root() -> Path:
    """Repository root, from ``REPO_ROOT`` (set by .envrc) or this file's tree."""
    env = os.environ.get("REPO_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def data_dir(environ: dict[str, str] | None = None) -> Path:
    """Output directory for generated artifacts (gitignored)."""
    override = _env("DEADLOCK_DATA_DIR", environ)
    return Path(override) if override else repo_root() / "data"


# Exposed to the .do scripts, which need these paths to declare dependencies.
# A named table beats `python -c '...'` in the build scripts: that is real code
# in a string, which no type checker or test ever sees.
RESOLVERS: Mapping[str, Callable[[], Path]] = {
    "game_dir": game_dir,
    "citadel_dir": citadel_dir,
    "vpk_dir_file": vpk_dir_file,
    "steam_inf": steam_inf,
    "data_dir": data_dir,
}


def main(argv: list[str] | None = None) -> None:
    """Print one named path: ``python -m deadlock.paths vpk_dir_file``."""
    [name] = (sys.argv if argv is None else argv)[1:]
    assert name in RESOLVERS, (name, sorted(RESOLVERS))
    _ = sys.stdout.write(f"{RESOLVERS[name]()}\n")


if __name__ == "__main__":
    main()
