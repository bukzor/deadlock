from pathlib import Path

import pytest

from .vo_soundevents import clips, hero_of, load

DOC = {
    "yamato_b_hero_3d": {
        "base": "Base.Hero.VO",
        "vsnd_files": "sounds/vo/yamato/b.vsnd",
    },
    "yamato_a_hero_3d": {
        "vsnd_files": ["sounds/vo/yamato/a1.vsnd", "sounds/vo/yamato/a2.vsnd"],
    },
    "yamato_silent_hero_3d": {"base": "Base.Hero.VO"},
}


class DescribeHeroOf:
    def it_is_the_file_name_suffix(self):
        path = Path("x/generated_vo_hero_yamato.vsndevts")
        assert hero_of(path) == "yamato"

    def it_rejects_a_non_hero_file(self):
        with pytest.raises(AssertionError, match="generated_vo_misc"):
            _ = hero_of(Path("generated_vo_misc.vsndevts"))


class DescribeClips:
    def it_lists_each_event_file_in_event_order(self):
        assert clips(DOC) == [
            ("yamato_a_hero_3d", "sounds/vo/yamato/a1.vsnd"),
            ("yamato_a_hero_3d", "sounds/vo/yamato/a2.vsnd"),
            ("yamato_b_hero_3d", "sounds/vo/yamato/b.vsnd"),
        ]

    def it_reads_a_null_root_as_no_events(self):
        assert clips(None) == []


class DescribeLoad:
    def it_parses_decompiled_kv3(self, tmp_path: Path):
        path = tmp_path / "generated_vo_hero_yamato.vsndevts"
        _ = path.write_text(
            "".join(
                [
                    "<!-- kv3 encoding:text:version{x} format:generic:version{y} -->\n",
                    "{\n\tyamato_b_hero_3d = \n\t{\n",
                    '\t\tvsnd_files = "sounds/vo/yamato/b.vsnd"\n\t}\n}\n',
                ]
            )
        )
        assert clips(load(path)) == [("yamato_b_hero_3d", "sounds/vo/yamato/b.vsnd")]
