"""Thin, deterministic wrapper around ValveResourceFormat's Source2Viewer-CLI.

VRF is the canonical Source 2 decompiler (the only thing that turns compiled
``_c`` resources into usable assets). We don't reimplement it; we build its argv
(pure, testable) and shell out (one impure ``run``). The binary is vendored under
``data/tools/`` and pinned — see ``docs/dev/environment.kb/toolchain.md``.

Flag reference: https://github.com/ValveResourceFormat/ValveResourceFormat
(note: VRF does not guarantee CLI flag stability across releases).
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

from . import paths


def binary_path(environ: dict[str, str] | None = None) -> Path:
    """Location of the Source2Viewer-CLI binary (override: ``DEADLOCK_S2V``)."""
    override = (environ if environ is not None else os.environ).get("DEADLOCK_S2V")
    return Path(override) if override else paths.data_dir(environ) / "tools/Source2Viewer-CLI"


def list_argv(vpk_dir_file: Path) -> list[str]:
    """Argv to list a VPK's contents as ``path CRC:… size:…`` lines."""
    return ["-i", str(vpk_dir_file), "--vpk_list"]


def extract_argv(
    vpk_dir_file: Path,
    out_dir: Path,
    *,
    decompile: bool = False,
    filepath: str | None = None,
    extensions: Sequence[str] = (),
) -> list[str]:
    """Argv to extract from a VPK into ``out_dir``.

    ``decompile`` converts ``_c`` resources to usable forms; ``filepath`` and
    ``extensions`` narrow what is extracted.
    """
    argv = ["-i", str(vpk_dir_file), "-o", str(out_dir)]
    if decompile:
        argv.append("-d")
    if filepath is not None:
        argv += ["-f", filepath]
    if extensions:
        argv += ["-e", ",".join(extensions)]
    return argv


def decompile_argv(input_file: Path, out_file: Path) -> list[str]:
    """Argv to decompile a single resource (e.g. ``a.vtex_c`` -> ``a.png``)."""
    return ["-i", str(input_file), "-o", str(out_file), "-d"]


def run(argv: Sequence[str], environ: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run Source2Viewer-CLI with ``argv`` (impure). Raises on non-zero exit."""
    binary = binary_path(environ)
    return subprocess.run(
        [str(binary), *argv],
        capture_output=True,
        text=True,
        check=True,
    )
