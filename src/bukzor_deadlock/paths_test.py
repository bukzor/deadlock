import re
from pathlib import Path

import pytest

from . import paths


class DescribeGameDir:
    def it_defaults_under_the_stock_steam_install(self):
        assert paths.game_dir({}) == paths.DEFAULT_HOME / "game"

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_HOME": "/games/deadlock"}
        assert paths.game_dir(env) == Path("/games/deadlock/game")


class DescribeVpkDirFile:
    def it_points_at_pak01_dir_under_citadel(self):
        env = {"DEADLOCK_HOME": "/g"}
        assert paths.vpk_dir_file(env) == Path("/g/game/citadel/pak01_dir.vpk")


class DescribePakDirFiles:
    def it_finds_every_game_dir_holding_a_pak_sorted(self, tmp_path: Path):
        for name in ("core", "citadel_french", "citadel"):
            (tmp_path / "game" / name).mkdir(parents=True)
            (tmp_path / "game" / name / "pak01_dir.vpk").touch()
        (tmp_path / "game/citadel_lv").mkdir()  # a locale dir without a pak
        env = {"DEADLOCK_HOME": str(tmp_path)}
        assert paths.pak_dir_files(env) == tuple(
            tmp_path / "game" / name / "pak01_dir.vpk"
            for name in ("citadel", "citadel_french", "core")
        )


class DescribeHeroNamesLoc:
    def it_points_at_the_english_hero_name_tokens(self):
        env = {"DEADLOCK_HOME": "/g"}
        loc = "/g/game/citadel/resource/localization/citadel_gc_hero_names"
        assert paths.hero_names_loc(env) == Path(
            f"{loc}/citadel_gc_hero_names_english.txt"
        )


class DescribeSteamInf:
    def it_points_at_steam_inf_under_citadel(self):
        env = {"DEADLOCK_HOME": "/g"}
        assert paths.steam_inf(env) == Path("/g/game/citadel/steam.inf")


class DescribeBinDirs:
    def it_lists_the_engine_then_the_game_bin_dir(self):
        env = {"DEADLOCK_HOME": "/g"}
        assert paths.bin_dirs(env) == (
            Path("/g/game/bin/win64"),
            Path("/g/game/citadel/bin/win64"),
        )


class DescribeMain:
    def it_prints_the_named_path(self, capsys: pytest.CaptureFixture[str]):
        paths.main(["paths", "vpk_dir_file"])
        assert capsys.readouterr().out == f"{paths.vpk_dir_file()}\n"

    def it_prints_a_path_list_one_per_line(self, capsys: pytest.CaptureFixture[str]):
        paths.main(["paths", "bin_dirs"])
        assert capsys.readouterr().out == "".join(f"{d}\n" for d in paths.bin_dirs())

    def it_fails_loudly_on_an_unknown_name(self):
        with pytest.raises(AssertionError, match="bogus"):
            paths.main(["paths", "bogus"])

    def it_resolves_every_name_the_do_scripts_use(self):
        do_scripts = Path(__file__).resolve().parents[2].glob("**/*.do")
        used = {
            match.group(1)
            for text in (p.read_text() for p in do_scripts)
            for match in re.finditer(r"bukzor_deadlock\.paths (\w+)", text)
        }
        assert used, "expected the .do scripts to resolve paths this way"
        assert used <= set(paths.RESOLVERS)


class DescribeFreeSpaceDir:
    def it_defaults_to_the_data_dir(self):
        assert paths.free_space_dir({}) == paths.data_dir({})

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_FREE_SPACE_DIR": "/mnt/c"}
        assert paths.free_space_dir(env) == Path("/mnt/c")


class DescribeDataDir:
    def it_defaults_under_the_repo_root(self):
        assert paths.data_dir({}) == paths.repo_root() / "data"

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_DATA_DIR": "/tmp/out"}
        assert paths.data_dir(env) == Path("/tmp/out")
