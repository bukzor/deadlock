import keyvalues3 as kv3

from .gamedata import records


class DescribeRecords:
    def it_emits_one_leaf_record_per_scalar(self):
        root = {"hero_a": {"hp": 100, "name": "A"}}
        assert list(records(root)) == [
            {"path": "hero_a.hp", "value": 100},
            {"path": "hero_a.name", "value": "A"},
        ]

    def it_indexes_sequences_in_the_path(self):
        root = {"hero_a": {"items": ["x", "y"]}}
        assert [r["path"] for r in records(root)] == [
            "hero_a.items[0]",
            "hero_a.items[1]",
        ]

    def it_unwraps_flagged_values_in_leaf_values(self):
        root = {"hero_a": {"model": kv3.flagged_value("models/a.vmdl")}}
        assert list(records(root)) == [
            {"path": "hero_a.model", "value": "models/a.vmdl"}
        ]
