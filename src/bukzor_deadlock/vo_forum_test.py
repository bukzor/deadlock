import csv
import io

from .vo_forum import HEADER, SPOKEN_OTHER, render, rows

NAMES = {"hero_tengu:n": "Ivy", "hero_ghost:n": "Lady Geist", "hero_yamato:n": "Yamato"}


def foreign(
    hero: str = "yamato",
    event: str = "yamato_a_01_hero_3d",
    lang: str = "ja",
    replacement: str = "こんにちは",
    translation: str = "Hello",
    doubt: str = "",
    source: str = "claude-fable-5-2",
) -> dict[str, str]:
    vsnd = f"sounds/vo/{hero}/{event}.vsnd"
    return {
        "hero": hero,
        "event": event,
        "vsnd": vsnd,
        "lang": lang,
        "replacement": replacement,
        "translation": translation,
        "doubt": doubt,
        "source": source,
    }


def lines(
    *rs: dict[str, str], english: str = "Speaks Japanese"
) -> list[dict[str, str]]:
    return [{"vsnd": r["vsnd"], "english": english} for r in rs]


class DescribeRows:
    def it_maps_a_plain_row(self) -> None:
        r = foreign()
        assert list(rows([r], lines(r), NAMES)) == [
            (
                "Yamato",
                "yamato_a_01_hero_3d",
                r["vsnd"],
                "Speaks Japanese",
                "こんにちは",
                "Hello",
                "",
            )
        ]

    def it_sorts_by_display_name_then_token(self) -> None:
        a = foreign("yamato", "yamato_b_hero_3d")
        b = foreign("yamato", "yamato_a_hero_3d")
        c = foreign("tengu", "tengu_z_hero_3d")
        out = list(rows([a, b, c], lines(a, b, c), NAMES))
        assert [(r[0], r[1]) for r in out] == [
            ("Ivy", "tengu_z_hero_3d"),
            ("Yamato", "yamato_a_hero_3d"),
            ("Yamato", "yamato_b_hero_3d"),
        ]

    def it_notes_doubt(self) -> None:
        r = foreign(doubt="small: x; turbo: y")
        [out] = rows([r], lines(r), NAMES)
        assert out[6] == "Doubtful. small: x; turbo: y"

    def it_notes_a_clip_the_owner_heard(self) -> None:
        r = foreign(source="@bukzor")
        [out] = rows([r], lines(r), NAMES)
        assert out[6] == "verified by ear"

    def it_notes_a_missing_caption(self) -> None:
        r = foreign(lang="auto")
        [out] = rows([r], lines(r, english=""), NAMES)
        assert (out[3], out[6]) == ("", "no caption in game")

    def it_names_a_spoken_language_the_caption_does_not(self) -> None:
        event = next(iter(SPOKEN_OTHER))
        r = foreign("tengu", event, "auto")
        [out] = rows([r], lines(r, english=""), NAMES)
        assert out[6] == "no caption in game; spoken in Spanish"

    def it_notes_ivys_pre_rename_name(self) -> None:
        r = foreign(
            "tengu", "tengu_ping_x_tengu_ping_2d", "auto", "Let's take out Tengu!"
        )
        [out] = rows([r], lines(r, english=""), NAMES)
        assert out[6] == "no caption in game; she says her pre-rename name, Tengu"

    def it_unescapes_cells(self) -> None:
        r = foreign(replacement="a\\nb")
        [out] = rows([r], lines(r), NAMES)
        assert out[4] == "a\nb"


class DescribeRender:
    def it_writes_bom_crlf_and_rfc4180_quotes(self) -> None:
        r = foreign(replacement='He said "hi", ok', translation="x")
        text = render(rows([r], lines(r), NAMES))
        assert text.startswith("﻿" + ",".join(HEADER) + "\r\n")
        [_, row] = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
        assert row[4] == 'He said "hi", ok'
        assert '"He said ""hi"", ok"' in text
