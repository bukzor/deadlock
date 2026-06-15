from .flatten import leaves


class DescribeLeaves:
    def it_yields_scalars_with_dotted_mapping_paths(self):
        assert list(leaves({"a": {"b": 1, "c": "x"}})) == [
            ("a.b", 1),
            ("a.c", "x"),
        ]

    def it_indexes_sequence_elements(self):
        assert list(leaves({"xs": [10, 20]})) == [
            ("xs[0]", 10),
            ("xs[1]", 20),
        ]

    def it_handles_nesting_of_mappings_and_sequences(self):
        assert list(leaves({"a": [{"b": 1}]})) == [("a[0].b", 1)]

    def it_represents_empty_containers_as_leaves(self):
        assert list(leaves({"empty_map": {}, "empty_list": []})) == [
            ("empty_map", {}),
            ("empty_list", []),
        ]

    def it_emits_a_bare_scalar_at_the_root(self):
        assert list(leaves(42)) == [("", 42)]
