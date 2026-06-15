from .gamedata import records


class DescribeRecords:
    def it_emits_mapping_entries_as_fields_with_a_key(self):
        root = {"hero_a": {"hp": 100, "name": "A"}}
        assert list(records(root)) == [{"_key": "hero_a", "hp": 100, "name": "A"}]

    def it_emits_scalar_entries_under_value(self):
        root = {"generic_data_type": "CitadelHeroData"}
        assert list(records(root)) == [
            {"_key": "generic_data_type", "_value": "CitadelHeroData"}
        ]

    def it_emits_one_record_per_top_level_entry(self):
        root = {"a": {"x": 1}, "b": {"x": 2}, "n": 3}
        out = list(records(root))
        assert [r["_key"] for r in out] == ["a", "b", "n"]

    def it_tags_records_with_source_when_given(self):
        root = {"a": {"x": 1}}
        assert list(records(root, source="scripts/heroes.vdata")) == [
            {"_file": "scripts/heroes.vdata", "_key": "a", "x": 1}
        ]
