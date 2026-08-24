"""Exercises bin/redo-adopt against a real redo build tree.

Skips unless `redo` is on PATH. Uses a scratch tree so it can't disturb this
repo's own build state.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ADOPT = Path(__file__).resolve().parents[1] / "bin/redo-adopt"

# `foo` records each build, so a rebuild is observable; `parent` reaches it via
# redo-ifchange, since naming a target on redo's command line always rebuilds it
_FOO_DO = """\
#!/bin/bash
set -euo pipefail
echo build >> builds.log
echo BUILT
"""
_PARENT_DO = """\
#!/bin/bash
set -euo pipefail
redo-ifchange foo
"""


def _builds(tree: Path) -> int:
    log = tree / "builds.log"
    return len(log.read_text().splitlines()) if log.exists() else 0


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    _ = (tmp_path / "foo.do").write_text(_FOO_DO)
    _ = (tmp_path / "parent.do").write_text(_PARENT_DO)
    _ = (tmp_path / "foo").write_text("HANDMADE\n")  # as a git checkout would leave it
    return tmp_path


def _redo(tree: Path, *args: str) -> None:
    _ = subprocess.run(["redo", *args], cwd=tree, check=True, capture_output=True)


def _adopt(tree: Path, *args: str) -> None:
    _ = subprocess.run([str(ADOPT), *args], cwd=tree, check=True, capture_output=True)


@pytest.mark.skipif(not shutil.which("redo"), reason="redo not installed")
class DescribeRedoAdopt:
    def it_leaves_an_unadopted_file_alone(self, tree: Path):
        """redo's own rule: never clobber a file it didn't generate."""
        _redo(tree, "parent")
        assert (tree / "foo").read_text() == "HANDMADE\n"
        assert _builds(tree) == 0

    def it_makes_redo_rebuild_a_file_it_did_not_generate(self, tree: Path):
        _adopt(tree, "foo")
        _redo(tree, "parent")
        assert (tree / "foo").read_text() == "BUILT\n"
        assert _builds(tree) == 1

    def it_is_a_noop_on_a_file_redo_already_owns(self, tree: Path):
        _adopt(tree, "foo")
        _redo(tree, "parent")
        _adopt(tree, "foo")  # second adopt must not re-dirty the target
        _redo(tree, "parent")
        assert _builds(tree) == 1

    def it_reclaims_an_edited_target_without_a_build_to_notice_first(self, tree: Path):
        """Adopting is enough on its own: no redo run in between."""
        _adopt(tree, "foo")
        _redo(tree, "parent")
        _ = (tree / "foo").write_text("TAMPERED\n")

        _adopt(tree, "foo")
        _redo(tree, "parent")
        assert (tree / "foo").read_text() == "BUILT\n"
        assert _builds(tree) == 2

    def it_reclaims_a_target_that_was_edited_by_hand(self, tree: Path):
        """redo demotes an edited target to a static file; adopting reclaims it."""
        _adopt(tree, "foo")
        _redo(tree, "parent")
        _ = (tree / "foo").write_text("TAMPERED\n")

        # redo notices the edit and refuses to trample it, recording the
        # override — which is the state adopt then reclaims
        _redo(tree, "parent")
        assert (tree / "foo").read_text() == "TAMPERED\n"
        assert _builds(tree) == 1

        _adopt(tree, "foo")
        _redo(tree, "parent")
        assert (tree / "foo").read_text() == "BUILT\n"
        assert _builds(tree) == 2

    def it_fails_on_a_missing_path(self, tree: Path):
        done = subprocess.run([str(ADOPT), "nope"], cwd=tree, capture_output=True, text=True)
        assert done.returncode != 0
        assert "no such file" in done.stderr

    def it_skips_a_missing_path_when_asked(self, tree: Path):
        _adopt(tree, "--if-exists", "nope", "foo")
        _redo(tree, "parent")
        assert _builds(tree) == 1
