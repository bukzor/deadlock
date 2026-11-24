import zlib
from pathlib import Path

import pytest

from .vo_lines import audio_file, main, rows


class DescribeAudioFile:
    def it_maps_a_vsnd_name_into_the_exploded_tree(self):
        assert audio_file(Path("vo.d"), "sounds/vo/yamato/a.vsnd") == Path(
            "vo.d/yamato/a.vsnd_c"
        )

    def it_rejects_a_clip_outside_sounds_vo(self):
        with pytest.raises(AssertionError, match="sounds/music/a.vsnd"):
            _ = audio_file(Path("vo.d"), "sounds/music/a.vsnd")


class DescribeRows:
    def it_joins_crc_and_caption_sorted_by_hero(self):
        clips = {
            "yamato": [("yamato_a", "sounds/vo/yamato/a.vsnd")],
            "haze": [("haze_b", "sounds/vo/haze/b.vsnd")],
            "warden": [("warden_c", "sounds/vo/warden/c.vsnd")],
        }
        crcs = {"sounds/vo/yamato/a.vsnd": 0xAB, "sounds/vo/haze/b.vsnd": 0x1}
        crcs |= {"sounds/vo/warden/c.vsnd": None}
        english = {"yamato_a": "Speaks\nJapanese"}
        assert list(rows(clips, crcs.__getitem__, english)) == [
            ("haze", "haze_b", "sounds/vo/haze/b.vsnd", "00000001", ""),
            ("warden", "warden_c", "sounds/vo/warden/c.vsnd", "", ""),
            (
                "yamato",
                "yamato_a",
                "sounds/vo/yamato/a.vsnd",
                "000000ab",
                "Speaks\\nJapanese",
            ),
        ]


class DescribeMain:
    def it_writes_the_table(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        events = tmp_path / "soundevents.d"
        events.mkdir()
        _ = (events / "generated_vo_hero_yamato.vsndevts").write_text(
            "".join(
                [
                    "{\n\tyamato_a = \n\t{\n\t\tvsnd_files = ",
                    '[ "sounds/vo/yamato/a.vsnd", "sounds/vo/yamato/gone.vsnd" ]\n\t}\n}\n',
                ]
            )
        )
        _ = (events / "generated_vo_misc.vsndevts").write_text("null\n")
        audio = tmp_path / "vo.d/yamato/a.vsnd_c"
        audio.parent.mkdir(parents=True)
        _ = audio.write_bytes(b"mp3")
        captions = tmp_path / "citadel_generated_vo_english.txt"
        _ = captions.write_text('"lang"\n{\n"Tokens"\n{\n"yamato_a" "Hi"\n}\n}\n')
        main(["vo_lines", str(events), str(tmp_path / "vo.d"), str(captions)])
        crc = f"{zlib.crc32(b'mp3'):08x}"
        assert capsys.readouterr().out == (
            "hero\tevent\tvsnd\tcrc32\tenglish\n"
            f"yamato\tyamato_a\tsounds/vo/yamato/a.vsnd\t{crc}\tHi\n"
            "yamato\tyamato_a\tsounds/vo/yamato/gone.vsnd\t\tHi\n"
        )
