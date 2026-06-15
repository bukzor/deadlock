from pathlib import Path

from .s2v import binary_path, decompile_argv, extract_argv, list_argv


class DescribeListArgv:
    def it_lists_a_vpk(self):
        assert list_argv(Path("/g/pak01_dir.vpk")) == [
            "-i",
            "/g/pak01_dir.vpk",
            "--vpk_list",
        ]


class DescribeExtractArgv:
    def it_extracts_raw_to_an_output_dir(self):
        assert extract_argv(Path("/g/p.vpk"), Path("/out")) == [
            "-i",
            "/g/p.vpk",
            "-o",
            "/out",
        ]

    def it_decompiles_and_filters_by_path_and_extensions(self):
        argv = extract_argv(
            Path("/g/p.vpk"),
            Path("/out"),
            decompile=True,
            filepath="scripts/abilities.vdata_c",
            extensions=("vtex_c", "vmdl_c"),
        )
        assert argv == [
            "-i",
            "/g/p.vpk",
            "-o",
            "/out",
            "-d",
            "-f",
            "scripts/abilities.vdata_c",
            "-e",
            "vtex_c,vmdl_c",
        ]


class DescribeDecompileArgv:
    def it_decompiles_one_resource_to_a_file(self):
        assert decompile_argv(Path("/in/a.vtex_c"), Path("/out/a.png")) == [
            "-i",
            "/in/a.vtex_c",
            "-o",
            "/out/a.png",
            "-d",
        ]


class DescribeBinaryPath:
    def it_defaults_under_the_data_tools_dir(self):
        assert binary_path({}) == Path(__file__).resolve().parents[2] / "data/tools/Source2Viewer-CLI"

    def it_honors_the_environment_override(self):
        assert binary_path({"DEADLOCK_S2V": "/opt/s2v"}) == Path("/opt/s2v")
