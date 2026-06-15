from pathlib import Path

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


class DescribeDataDir:
    def it_defaults_under_the_repo_root(self):
        assert paths.data_dir({}) == paths.repo_root() / "data"

    def it_honors_the_environment_override(self):
        env = {"DEADLOCK_DATA_DIR": "/tmp/out"}
        assert paths.data_dir(env) == Path("/tmp/out")
