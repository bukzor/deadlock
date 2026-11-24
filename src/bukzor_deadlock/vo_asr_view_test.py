import pytest

from .vo_asr_ledger import Row
from .vo_asr_view import Fixup, parse_fixups, rows

SMALL, TURBO = "small/dtw/greedy", "large-v3-turbo/beam5"


def line(event: str, crc32: str, english: str = "Speaks Japanese") -> dict[str, str]:
    vsnd = f"sounds/vo/yamato/{event}.vsnd"
    return {
        "hero": "yamato",
        "event": event,
        "vsnd": vsnd,
        "crc32": crc32,
        "english": english,
    }


def asr(crc32: str, model: str, text: str) -> Row:
    return Row(crc32, f"sounds/vo/yamato/{crc32}.vsnd", model, text)


def fixup(replacement: str, by: str = "claude-opus-5.5", doubt: str = "") -> Fixup:
    return Fixup(replacement, f"means {replacement}", doubt, by)


class DescribeRows:
    def it_prefers_the_strongest_model_whose_text_has_a_fixup(self):
        ledger = [asr("0000000a", SMALL, "s"), asr("0000000a", TURBO, "t")]
        fixups = {"s": fixup("S"), "t": fixup("T", by="@bukzor")}
        got = list(rows([line("a", "0000000a")], {"yamato": ledger}, fixups))
        assert got == [
            (
                "yamato",
                "a",
                "sounds/vo/yamato/a.vsnd",
                "ja",
                "T",
                "means T",
                "",
                "@bukzor",
            )
        ]

    def it_labels_each_row_with_its_clips_language(self):
        lines = [{**line("a", "0000000a", "Speaks spanish"), "hero": "tengu"}]
        got = list(rows(lines, {"tengu": []}, {}))
        assert [row[:4] for row in got] == [
            ("tengu", "a", "sounds/vo/yamato/a.vsnd", "es")
        ]

    def it_takes_a_weaker_models_fixup_over_unfixed_text(self):
        ledger = [asr("0000000a", TURBO, "t"), asr("0000000a", SMALL, "s")]
        got = list(rows([line("a", "0000000a")], {"yamato": ledger}, {"s": fixup("S")}))
        assert [row[4:] for row in got] == [("S", "means S", "", "claude-opus-5.5")]

    def it_ranks_detected_rows_by_their_model(self):
        ledger = [asr("0000000a", TURBO + "/auto", "t"), asr("0000000a", SMALL, "s")]
        ledger += [asr("0000000a", SMALL + "/auto", "s")]
        fixups = {"s": fixup("S"), "t": fixup("T")}
        got = list(rows([line("a", "0000000a")], {"yamato": ledger}, fixups))
        assert [row[4] for row in got] == ["T"]

    def it_carries_the_doubt_of_the_fixup_that_wins(self):
        ledger = [asr("0000000a", TURBO, "t"), asr("0000000a", SMALL, "s")]
        fixups = {"s": fixup("S", doubt="small heard S"), "t": fixup("T")}
        got = list(rows([line("a", "0000000a")], {"yamato": ledger}, fixups))
        assert [row[4:] for row in got] == [("T", "means T", "", "claude-opus-5.5")]
        got = list(
            rows([line("a", "0000000a")], {"yamato": ledger}, {"s": fixups["s"]})
        )
        assert [row[4:] for row in got] == [
            ("S", "means S", "small heard S", "claude-opus-5.5")
        ]

    def it_shows_the_strongest_asr_text_until_a_fixup_lands(self):
        ledger = [asr("0000000a", TURBO, "t\tx"), asr("0000000a", SMALL, "s")]
        got = list(rows([line("a", "0000000a")], {"yamato": ledger}, {}))
        assert [row[4:] for row in got] == [("t\\tx", "", "", TURBO)]

    def it_lists_a_clip_with_no_asr_yet_with_empty_cells(self):
        got = list(rows([line("a", "0000000a")], {"yamato": []}, {}))
        assert [row[4:] for row in got] == [("", "", "", "")]

    def it_gives_each_event_of_a_shared_clip_a_row(self):
        lines = [line("a", "0000000a"), line("b", "0000000a")]
        ledger = [asr("0000000a", SMALL, "s")]
        assert [row[1] for row in rows(lines, {"yamato": ledger}, {})] == ["a", "b"]

    def it_skips_clips_out_of_scope_and_heroes_with_no_ledger(self):
        lines = [line("a", "0000000a", english="Careful!"), line("j", "0000000b")]
        lines += [{**line("h", "0000000c"), "hero": "haze"}]
        ledger = [asr("0000000b", SMALL, "s")]
        assert [row[1] for row in rows(lines, {"yamato": ledger}, {})] == ["j"]

    def it_rejects_an_unknown_model(self):
        with pytest.raises(AssertionError, match="tiny"):
            _ = list(
                rows(
                    [line("a", "0000000a")],
                    {"yamato": [asr("0000000a", "tiny", "")]},
                    {},
                )
            )


class DescribeParseFixups:
    def it_keys_rows_by_their_unescaped_asr_text(self):
        text = "asr_text\treplacement\ttranslation\tdoubt\tby\na\\tb\tR\tT\t\t@bukzor\n"
        assert parse_fixups(text) == {"a\tb": Fixup("R", "T", "", "@bukzor")}

    def it_keeps_a_doubt_reason_with_its_row(self):
        text = (
            "asr_text\treplacement\ttranslation\tdoubt\tby\nS\tR\tT\tunsure\t@bukzor\n"
        )
        assert parse_fixups(text) == {"S": Fixup("R", "T", "unsure", "@bukzor")}

    def it_rejects_a_file_with_another_header(self):
        with pytest.raises(AssertionError, match="crc32"):
            _ = parse_fixups("crc32\treplacement\ttranslation\tdoubt\tby\n")
