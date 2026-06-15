import keyvalues3 as kv3

from .jsonl import dump_lines, dumps, to_jsonable


class DescribeToJsonable:
    def it_passes_through_json_native_scalars(self):
        assert to_jsonable({"a": 1, "b": [True, "x", 1.5]}) == {
            "a": 1,
            "b": [True, "x", 1.5],
        }

    def it_unwraps_kv3_flagged_values_to_their_value(self):
        fv = kv3.flagged_value("models/hero.vmdl")
        assert to_jsonable({"model": fv}) == {"model": "models/hero.vmdl"}

    def it_recurses_into_nested_flagged_values(self):
        assert to_jsonable([{"n": kv3.flagged_value(7)}]) == [{"n": 7}]


class DescribeDumps:
    def it_emits_compact_sorted_single_line_json(self):
        assert dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'


class DescribeDumpLines:
    def it_writes_one_json_object_per_line(self):
        assert dump_lines([{"a": 1}, {"b": 2}]) == '{"a":1}\n{"b":2}\n'
