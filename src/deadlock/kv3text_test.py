from pathlib import Path

import keyvalues3
import pytest

from . import jsonl
from .kv3text import parse

_HEADER = (
    "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d}"
    " format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"
)

# large files are excluded to keep the oracle (keyvalues3, ~4s/MB) affordable
_CORPUS = Path(__file__).parent.parent.parent / "data" / "gamedata"
_ORACLE_BUDGET = 200_000


class DescribeParse:
    def it_parses_scalars(self):
        assert parse(_HEADER + '{ s = "x" i = 3 f = 1.5 neg = -2 }') == {
            "s": "x",
            "i": 3,
            "f": 1.5,
            "neg": -2,
        }

    def it_parses_null_and_booleans(self):
        assert parse(_HEADER + "{ a = null b = true c = false }") == {
            "a": None,
            "b": True,
            "c": False,
        }

    def it_parses_nested_containers(self):
        assert parse(_HEADER + "{ m = { xs = [1, [2], {}] e = [] } }") == {
            "m": {"xs": [1, [2], {}], "e": []}
        }

    def it_allows_a_trailing_comma_and_no_comma_before_close(self):
        assert parse(_HEADER + "[ 1, 2, ]") == [1, 2]
        assert parse(_HEADER + "[ 1, 2 ]") == [1, 2]

    def it_unescapes_quoted_strings_like_keyvalues3(self):
        assert parse(_HEADER + r'{ k = "You\'re \"A\"\n\tdone\\" }') == {
            "k": "You're \"A\"\n\tdone\\"
        }

    def it_accepts_quoted_keys(self):
        assert parse(_HEADER + '{ "You\\\'re Welcome" = 1 }') == {"You're Welcome": 1}

    def it_drops_value_flags(self):
        assert parse(_HEADER + '{ a = subclass:"x" b = resource|subclass:"y" }') == {
            "a": "x",
            "b": "y",
        }

    def it_parses_multiline_strings(self):
        assert parse(_HEADER + '{ k = """\nline1\nline2""" }') == {
            "k": "line1\nline2"
        }

    def it_rejects_junk(self):
        with pytest.raises((AssertionError, ValueError)):
            parse(_HEADER + "{ a = bogus }")

    class WhenComparedToKeyvalues3:
        @pytest.mark.parametrize(
            "path",
            sorted(
                p.relative_to(_CORPUS)
                for p in _CORPUS.rglob("*.vdata")
                if p.stat().st_size <= _ORACLE_BUDGET
            )
            if _CORPUS.is_dir()
            else [],
            ids=str,
        )
        def it_matches_on_extracted_game_data(self, path: Path):
            text = (_CORPUS / path).read_text(encoding="utf-8")
            oracle: object = keyvalues3.read(_CORPUS / path).value
            assert jsonl.to_jsonable(parse(text)) == jsonl.to_jsonable(oracle)

        def it_has_a_corpus_to_compare_against(self):
            assert _CORPUS.is_dir(), _CORPUS
