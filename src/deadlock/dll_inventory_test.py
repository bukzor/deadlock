import re
from pathlib import Path

import pytest

from . import dll_inventory
from .dll_inventory import dlls


def touch(game: Path, *relpaths: str) -> None:
    for relpath in relpaths:
        path = game / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


class DescribeDlls:
    def it_lists_paths_relative_to_game(self, tmp_path: Path):
        touch(tmp_path, "citadel/bin/win64/server.dll")
        assert dlls(tmp_path) == ["citadel/bin/win64/server.dll"]

    def it_finds_dlls_in_nested_dirs(self, tmp_path: Path):
        touch(
            tmp_path,
            "bin/win64/tier0.dll",
            "bin/win64/qt5_plugins/platforms/qwindows.dll",
            "bin/win64/subtools/tool.dll",
        )
        assert dlls(tmp_path) == [
            "bin/win64/qt5_plugins/platforms/qwindows.dll",
            "bin/win64/subtools/tool.dll",
            "bin/win64/tier0.dll",
        ]

    def it_ignores_non_dll_files(self, tmp_path: Path):
        touch(tmp_path, "a.dll", "a.pdb", "dll", "b.dll.bak", "c.dll.txt")
        assert dlls(tmp_path) == ["a.dll"]

    def it_ignores_a_directory_named_like_a_dll(self, tmp_path: Path):
        (tmp_path / "x.dll").mkdir()
        assert dlls(tmp_path) == []

    def it_sorts_by_bytes(self, tmp_path: Path):
        touch(tmp_path, "b.dll", "SDL3.dll", "a.dll", "Qt5Core.dll")
        assert dlls(tmp_path) == ["Qt5Core.dll", "SDL3.dll", "a.dll", "b.dll"]

    def it_keeps_an_uppercase_suffix(self, tmp_path: Path):
        touch(tmp_path, "a.DLL", "b.Dll")
        assert dlls(tmp_path) == ["a.DLL", "b.Dll"]

    def it_lists_a_dll_once_under_a_symlinked_dir(self, tmp_path: Path):
        touch(tmp_path, "addons/replays/r.dll")
        (tmp_path / "replays").symlink_to(tmp_path / "addons/replays")
        assert dlls(tmp_path) == ["addons/replays/r.dll"]

    class WhenBasenamesCollide:
        def it_fails_naming_the_duplicates(self, tmp_path: Path):
            touch(tmp_path, "a/server.dll", "b/server.dll", "c/client.dll")
            duplicates = {"server.dll": ["a/server.dll", "b/server.dll"]}
            with pytest.raises(AssertionError, match=f"^{re.escape(str(duplicates))}"):
                _ = dlls(tmp_path)

        def it_compares_basenames_ignoring_case(self, tmp_path: Path):
            touch(tmp_path, "a/Qt5Core.dll", "b/qt5core.DLL")
            with pytest.raises(AssertionError, match="a/Qt5Core.dll"):
                _ = dlls(tmp_path)


class DescribeMain:
    def it_prints_dlls_list(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        touch(tmp_path, "game/bin/win64/b.dll", "game/citadel/bin/win64/a.dll")
        monkeypatch.setenv("DEADLOCK_HOME", str(tmp_path))
        dll_inventory.main(["dll_inventory"])
        assert capsys.readouterr().out == (
            "bin/win64/b.dll\ncitadel/bin/win64/a.dll\n"
        )
