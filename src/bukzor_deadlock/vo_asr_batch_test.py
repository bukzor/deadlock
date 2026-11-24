import math

from .vo_asr_batch import Token, Transcript, cuts, pack, split


def token(text: str, t_dtw: int, start_ms: int = 0) -> Token:
    return {"text": text, "t_dtw": t_dtw, "offsets": {"from": start_ms}}


def transcript(*segments: list[Token]) -> Transcript:
    return {"transcription": [{"tokens": tokens} for tokens in segments]}


def fragment(raw: bytes) -> str:
    """A token text as whisper's JSON holds a partial UTF-8 character."""
    return raw.decode("utf-8", errors="surrogateescape")


class DescribePack:
    def it_fills_each_batch_up_to_the_window_counting_gaps(self):
        assert pack([9, 9, 9, 9], window=30, gap=1) == [[0, 1, 2], [3]]
        assert pack([14, 14], window=30, gap=1) == [[0, 1]]
        assert pack([14, 14.5], window=30, gap=1) == [[0], [1]]

    def it_caps_the_clips_per_batch(self):
        assert pack([1, 1, 1], window=30, gap=1, most=2) == [[0, 1], [2]]

    def it_gives_an_overlong_clip_a_batch_of_its_own(self):
        assert pack([2, 40, 2], window=30, gap=1) == [[0], [1], [2]]


class DescribeCuts:
    def it_cuts_each_slot_in_the_middle_of_the_gap_after_its_clip(self):
        assert cuts([2, 3, 4], gap=1) == [2.5, 6.5, math.inf]


class DescribeSplit:
    def it_assigns_each_token_to_the_slot_holding_its_dtw_time(self):
        doc = transcript([token(" a", 240), token(" b", 260)], [token(" c", 700)])
        assert split(doc, [2.5, 6.5, math.inf]) == ["a", "b", "c"]

    def it_keeps_punctuation_with_the_token_before_it(self):
        doc = transcript([token("a", 100), token("。", 300), token("b", 300)])
        assert split(doc, [2.5, math.inf]) == ["a。", "b"]

    def it_places_leading_punctuation_by_its_own_time(self):
        doc = transcript([token("「", 300), token("b", 300)])
        assert split(doc, [2.5, 6.5, math.inf]) == ["", "「b", ""]

    def it_falls_back_to_the_start_offset_without_dtw_time(self):
        doc = transcript([token("a", -1, start_ms=3000)])
        assert split(doc, [2.5, math.inf]) == ["", "a"]

    def it_skips_special_tokens(self):
        doc = transcript([token("[_BEG_]", 0), token("a", 10), token("[_TT_150]", 20)])
        assert split(doc, [math.inf]) == ["a"]

    def it_joins_utf8_fragments_into_characters(self):
        raw = "刀".encode()
        doc = transcript([token(fragment(raw[:2]), 10), token(fragment(raw[2:]), 20)])
        assert split(doc, [math.inf]) == ["刀"]
