import re
from pathlib import Path

import pytest

from . import paths


class DescribeGameDir:
    def it_defaults_to_the_stock_steam_install(self):
        assert paths.game_dir({}) == paths.DEFAULT_GAME_DIR

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_GAME_DIR": "/games/deadlock/game"}
        assert paths.game_dir(env) == Path("/games/deadlock/game")


class DescribeVpkDirFile:
    def it_points_at_pak01_dir_under_citadel(self):
        env = {"DEADLOCK_GAME_DIR": "/g"}
        assert paths.vpk_dir_file(env) == Path("/g/citadel/pak01_dir.vpk")


class DescribeSteamInf:
    def it_points_at_steam_inf_under_citadel(self):
        env = {"DEADLOCK_GAME_DIR": "/g"}
        assert paths.steam_inf(env) == Path("/g/citadel/steam.inf")


class DescribeMain:
    def it_prints_the_named_path(self, capsys: pytest.CaptureFixture[str]):
        paths.main(["paths", "vpk_dir_file"])
        assert capsys.readouterr().out == f"{paths.vpk_dir_file()}\n"

    def it_fails_loudly_on_an_unknown_name(self):
        with pytest.raises(AssertionError, match="bogus"):
            paths.main(["paths", "bogus"])

    def it_resolves_every_name_the_do_scripts_use(self):
        do_scripts = Path(__file__).resolve().parents[2].glob("**/*.do")
        used = {
            match.group(1)
            for text in (p.read_text() for p in do_scripts)
            for match in re.finditer(r"deadlock\.paths (\w+)", text)
        }
        assert used, "expected the .do scripts to resolve paths this way"
        assert used <= set(paths.RESOLVERS)


class DescribeDataDir:
    def it_defaults_under_the_repo_root(self):
        assert paths.data_dir({}) == paths.repo_root() / "data"

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_DATA_DIR": "/tmp/out"}
        assert paths.data_dir(env) == Path("/tmp/out")
