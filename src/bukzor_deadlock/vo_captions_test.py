from pathlib import Path

from .vo_captions import lang_of, rows, tokens

TEXT = (
    '﻿"lang"\r\n'
    "{\r\n"
    '\t"Language"\t\t"English"\r\n'
    '\t"Tokens"\r\n'
    "\t{\r\n"
    '\t\t"yamato_ping_01_hero_3d"\t\t"Speaks Japanese"\r\n'
    '\t\t"astro_kill_chrono_03_hero_3d"\t\t"\\"Time Thief,\\" please."\r\n'
    "\t}\r\n"
    "}\r\n"
)
STUB = '"lang"\n{\n\t"Language"\t\t"danish"\n\t"Tokens"\n\t{\n\t\t\n\t}\n}\n'


class DescribeTokens:
    def it_reads_the_token_table(self):
        assert tokens(TEXT) == {
            "yamato_ping_01_hero_3d": "Speaks Japanese",
            "astro_kill_chrono_03_hero_3d": '"Time Thief," please.',
        }

    def it_reads_a_stub_as_empty(self):
        assert tokens(STUB) == {}

    def it_keeps_a_newline_in_a_caption(self):
        text = TEXT.replace("Speaks Japanese", "wanted \r\nyou")
        assert tokens(text)["yamato_ping_01_hero_3d"] == "wanted \r\nyou"


class DescribeLangOf:
    def it_is_the_file_name_suffix(self):
        path = Path("x/citadel_generated_vo_koreana.txt")
        assert lang_of(path) == "koreana"


class DescribeRows:
    def it_is_long_by_locale_sorted_by_event_then_lang(self):
        tables = {
            "french": {"b": "B-fr", "a": "A-fr"},
            "english": {"a": "A\nen"},
            "danish": {},
        }
        assert list(rows(tables)) == [
            ("a", "english", "A\\nen"),
            ("a", "french", "A-fr"),
            ("b", "french", "B-fr"),
        ]
