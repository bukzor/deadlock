import io
from pathlib import Path

import pytest

from . import dlls_list

LISTING = [
    "bin/win64/qt5_plugins/platforms/qwindows.dll\n",
    "bin/win64/tier0.dll\n",
    "citadel/bin/win64/server.dll\n",
]


class DescribeRelpath:
    def it_finds_the_entry_by_basename(self):
        assert (
            dlls_list.relpath(LISTING, "server.dll") == "citadel/bin/win64/server.dll"
        )

    def it_finds_a_nested_entry(self):
        assert (
            dlls_list.relpath(LISTING, "qwindows.dll")
            == "bin/win64/qt5_plugins/platforms/qwindows.dll"
        )

    def it_fails_loudly_on_an_unlisted_name(self):
        with pytest.raises(AssertionError, match="client.dll"):
            _ = dlls_list.relpath(LISTING, "client.dll")

    def it_rejects_a_path_given_as_the_name(self):
        with pytest.raises(AssertionError, match="server.dll"):
            _ = dlls_list.relpath(LISTING, "citadel/bin/win64/server.dll")

    def it_rejects_a_suffix_of_a_listed_basename(self):
        with pytest.raises(AssertionError, match="ier0.dll"):
            _ = dlls_list.relpath(LISTING, "ier0.dll")


class DescribeMain:
    def it_prints_the_dll_path_under_game_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        monkeypatch.setenv("DEADLOCK_HOME", "/g")
        monkeypatch.setattr("sys.stdin", io.StringIO("".join(LISTING)))
        dlls_list.main(["dlls_list", "server.dll"])
        expected = Path("/g/game/citadel/bin/win64/server.dll")
        assert capsys.readouterr().out == f"{expected}\n"
