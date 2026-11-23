import io
import json
from pathlib import Path

import pytest

from . import dll_closure

LISTING = [
    "bin/win64/Qt5Core.dll\n",
    "bin/win64/tier0.dll\n",
    "citadel/bin/win64/server.dll\n",
]
SERVER = {
    "outcome": "ok",
    "modules": ["server.dll", "tier0.dll"],
}


class DescribeClosure:
    def it_lists_the_entries_of_the_modules_the_load_added(self):
        assert dll_closure.closure(LISTING, SERVER) == [
            "bin/win64/tier0.dll",
            "citadel/bin/win64/server.dll",
        ]

    def it_matches_the_basename_ignoring_case(self):
        document = {"outcome": "ok", "modules": ["QT5core.DLL"]}
        assert dll_closure.closure(LISTING, document) == ["bin/win64/Qt5Core.dll"]

    @pytest.mark.parametrize("module", ["ier0.dll", "win64/tier0.dll", "shell32.dll"])
    def it_rejects_a_module_the_listing_does_not_name(self, module: str):
        document = {"outcome": "ok", "modules": ["tier0.dll", module]}
        with pytest.raises(AssertionError, match="not in dlls.list"):
            _ = dll_closure.closure(LISTING, document)

    def it_is_empty_for_a_failed_load(self):
        document = {"outcome": "failed", "error": "LoadLibraryExW: 126"}
        assert dll_closure.closure(LISTING, document) == []

    def it_rejects_an_excluded_dll(self):
        document = {"outcome": "excluded", "reason": "hangs"}
        with pytest.raises(AssertionError, match="excluded"):
            _ = dll_closure.closure(LISTING, document)

    def it_rejects_a_module_that_is_not_a_name(self):
        document = {"outcome": "ok", "modules": [7]}
        with pytest.raises(AssertionError, match="7"):
            _ = dll_closure.closure(LISTING, document)


class DescribeMain:
    def it_prints_each_dll_path_under_game_dir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        load = tmp_path / "server.dll.json"
        _ = load.write_text(json.dumps(SERVER))
        monkeypatch.setenv("DEADLOCK_HOME", "/g")
        monkeypatch.setattr("sys.stdin", io.StringIO("".join(LISTING)))
        dll_closure.main(["dll_closure", str(load)])
        game = Path("/g/game")
        assert capsys.readouterr().out == (
            f"{game / 'bin/win64/tier0.dll'}\n{game / 'citadel/bin/win64/server.dll'}\n"
        )
