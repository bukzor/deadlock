from collections.abc import Mapping
from io import StringIO

import keyvalues3 as kv3
import pytest

from .gamedata import dumps, load


class DescribeDumps:
    def it_keeps_source_key_order(self):
        assert list(load(StringIO(dumps({"b": 1, "a": 2})))) == ["b", "a"]

    def it_unwraps_flagged_values(self):
        root = {"hero_a": {"model": kv3.flagged_value("models/a.vmdl")}}
        assert load(StringIO(dumps(root))) == {"hero_a": {"model": "models/a.vmdl"}}

    def it_puts_each_scalar_on_its_own_line(self):
        assert dumps({"a": {"b": 1, "c": [2]}}).splitlines() == [
            "{",
            '  "a": {',
            '    "b": 1,',
            '    "c": [',
            "      2",
            "    ]",
            "  }",
            "}",
        ]


class DescribeLoad:
    def it_round_trips_dumps(self):
        root: Mapping[str, object] = {"hero_a": {"hp": 100, "items": ["x", "y"], "empty": {}}}
        assert load(StringIO(dumps(root))) == root

    def it_requires_a_mapping_root(self):
        with pytest.raises(AssertionError):
            _ = load(StringIO("[]"))
