import pytest

from .vo_asr_ledger import Clip, Row, clips, merge, parse, pending, render


def line(event: str, crc32: str, english: str, hero: str = "yamato") -> dict[str, str]:
    vsnd = f"sounds/vo/{hero}/{event}.vsnd"
    return {
        "hero": hero,
        "event": event,
        "vsnd": vsnd,
        "crc32": crc32,
        "english": english,
    }


def clip(event: str, crc32: str) -> Clip:
    return Clip(crc32, f"sounds/vo/yamato/{event}.vsnd")


class DescribeClips:
    def it_takes_japanese_and_uncaptioned_clips_but_not_emotes(self):
        lines = [
            line("a", "0000000a", "Speaks Japanese"),
            line("b", "0000000b", "Careful, Calico!"),
            line("c", "0000000c", ""),
            line("emote/d", "0000000d", ""),
        ]
        assert clips(lines, "yamato") == [clip("a", "0000000a"), clip("c", "0000000c")]

    def it_takes_only_the_named_hero(self):
        lines = [line("a", "0000000a", "Speaks Japanese", hero="haze")]
        assert clips(lines, "yamato") == []

    def it_takes_nothing_from_a_hero_with_no_japanese_lines(self):
        assert clips([line("c", "0000000c", "")], "yamato") == []

    def it_keys_a_repeated_clip_once_under_its_first_name(self):
        lines = [
            line("b", "0000000a", "Speaks Japanese"),
            line("a", "0000000a", "Speaks Japanese"),
            line("c", "0000000a", "Speaks Japanese"),
        ]
        assert clips(lines, "yamato") == [clip("a", "0000000a")]

    def it_skips_a_clip_the_paks_do_not_ship(self):
        assert clips([line("a", "", "Speaks Japanese")], "yamato") == []


class DescribePending:
    def it_lists_the_clips_with_no_row_for_the_model(self):
        ledger = [
            Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "x"),
            Row("0000000b", "sounds/vo/yamato/b.vsnd", "turbo", "y"),
        ]
        wanted = [clip("a", "0000000a"), clip("b", "0000000b")]
        assert pending(wanted, ledger, "small") == [clip("b", "0000000b")]


class DescribeMerge:
    def it_replaces_a_row_of_the_same_clip_and_model(self):
        old = [Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "old")]
        new = [Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "new")]
        assert merge(old, new, [clip("a", "0000000a")]) == new

    def it_keeps_each_models_row_sorted_by_clip_then_model(self):
        a_small = Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "x")
        a_turbo = Row("0000000a", "sounds/vo/yamato/a.vsnd", "turbo", "y")
        b_small = Row("00000001", "sounds/vo/yamato/b.vsnd", "small", "z")
        wanted = [clip("a", "0000000a"), clip("b", "00000001")]
        merged = merge([b_small, a_turbo], [a_small], wanted)
        assert merged == [a_small, a_turbo, b_small]

    def it_drops_rows_whose_clip_has_left_the_scope(self):
        gone = Row("0000000f", "sounds/vo/yamato/f.vsnd", "small", "x")
        assert merge([gone], [], [clip("a", "0000000a")]) == []

    def it_renames_a_row_after_its_clip(self):
        old = [Row("0000000a", "sounds/vo/yamato/old.vsnd", "small", "x")]
        merged = merge(old, [], [clip("a", "0000000a")])
        assert merged == [Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "x")]


class DescribeLedgerText:
    def it_round_trips_text_that_needs_escaping(self):
        rows = [Row("0000000a", "sounds/vo/yamato/a.vsnd", "small", "a\tb\\n\nc")]
        text = render(rows)
        assert text.count("\n") == 2, text
        assert parse(text) == rows

    def it_starts_with_a_header(self):
        assert render([]) == "crc32\tvsnd\tmodel\ttext\n"

    def it_rejects_a_file_with_another_header(self):
        with pytest.raises(AssertionError, match="hero"):
            _ = parse("hero\tvsnd\tmodel\ttext\n")
