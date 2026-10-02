import pytest

from .flatten import leaves, tree, unflatten

NESTED = {
    "a": {"b": 1, "c": "x"},
    "xs": [10, 20, {"deep": [True, None]}],
    "empty_map": {},
    "empty_list": [],
    "n": {"2": "digit-named key"},
}


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

    def it_quotes_keys_that_contain_path_syntax(self):
        assert list(leaves({"Impact.Concrete": {"x": 1}})) == [('["Impact.Concrete"].x', 1)]

    def it_quotes_a_nested_awkward_key_after_its_parent(self):
        assert list(leaves({"a": {"b.c": 1}})) == [('a["b.c"]', 1)]

    def it_quotes_the_empty_key(self):
        assert list(leaves({"": 1})) == [('[""]', 1)]


class DescribeUnflatten:
    def it_rebuilds_mappings(self):
        assert unflatten([("a.b", 1), ("a.c", "x")]) == {"a": {"b": 1, "c": "x"}}

    def it_rebuilds_sequences(self):
        assert unflatten([("xs[0]", 10), ("xs[1]", 20)]) == {"xs": [10, 20]}

    def it_rebuilds_nesting_of_mappings_and_sequences(self):
        assert unflatten([("a[0].b", 1)]) == {"a": [{"b": 1}]}

    def it_restores_empty_containers(self):
        assert unflatten([("empty_map", {}), ("empty_list", [])]) == {"empty_map": {}, "empty_list": []}

    def it_restores_a_bare_scalar_root(self):
        assert unflatten([("", 42)]) == 42

    def it_keeps_digit_named_keys_as_mapping_keys(self):
        assert unflatten([("n.2", "v")]) == {"n": {"2": "v"}}

    def it_inverts_leaves(self):
        assert unflatten(leaves(NESTED)) == NESTED

    @pytest.mark.parametrize("key", ["a.b", "a[0]", "a]", "", 'q"uote', "back\\slash", "ünï", "0"])
    def it_inverts_leaves_for_awkward_keys(self, key: str):
        value = {key: {"x": 1}, "y": {key: [2, {key: 3}]}}
        assert unflatten(sorted(leaves(value))) == value

    def it_accepts_rows_in_sorted_order(self):
        # the flat files are byte-sorted, so xs[10] precedes xs[2]
        rows = sorted(leaves({"xs": list(range(12))}))
        assert unflatten(rows) == {"xs": list(range(12))}

    def it_fails_on_a_missing_sequence_index(self):
        with pytest.raises(AssertionError, match="xs"):
            _ = unflatten([("xs[1]", 5)])

    def it_fails_when_a_path_is_both_leaf_and_container(self):
        with pytest.raises(AssertionError, match="a"):
            _ = unflatten([("a", 1), ("a.b", 2)])

    def it_fails_when_a_node_mixes_keys_and_indices(self):
        with pytest.raises(AssertionError, match="a"):
            _ = unflatten([("a.b", 1), ("a[0]", 2)])

    def it_fails_on_a_duplicate_path(self):
        with pytest.raises(AssertionError, match="a"):
            _ = unflatten([("a", 1), ("a", 2)])

    def it_fails_on_no_rows(self):
        with pytest.raises(AssertionError):
            _ = unflatten([])

    def it_fails_on_a_path_it_cannot_parse(self):
        with pytest.raises(AssertionError, match=r"a\.\.b"):
            _ = unflatten([("a..b", 1)])


class DescribeTree:
    def it_unflattens_jsonl_records_into_the_root_mapping(self):
        records = [{"path": "a.b", "value": 1}, {"path": "a.c", "value": 2}]
        assert tree(records) == {"a": {"b": 1, "c": 2}}

    def it_requires_string_paths(self):
        with pytest.raises(AssertionError, match="7"):
            _ = tree([{"path": 7, "value": 1}])

    def it_requires_a_mapping_root(self):
        with pytest.raises(AssertionError):
            _ = tree([{"path": "", "value": 42}])
