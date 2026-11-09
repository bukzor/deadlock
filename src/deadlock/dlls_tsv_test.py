import json
from pathlib import Path

import pytest

from .dlls_tsv import NULL, cell, is_str_sequence, list_cell, load_documents, uncell, unlist_cell
from .types import is_sequence


class DescribeCell:
    def it_keeps_plain_text(self):
        assert cell("Heals the player.") == "Heals the player."

    def it_escapes_tab_newline_return_and_backslash(self):
        assert cell("a\tb\nc\rd\\e") == "a\\tb\\nc\\rd\\\\e"

    def it_renders_null_as_backslash_n(self):
        assert cell(None) == NULL == "\\N"

    def it_keeps_the_empty_string_distinct_from_null(self):
        assert cell("") == ""

    def it_keeps_a_literal_backslash_n_distinct_from_null(self):
        assert cell("\\N") == "\\\\N"


class DescribeUncell:
    @pytest.mark.parametrize(
        "value", [None, "", "\\N", "\\", "a\\", "\\\\N", "a\\nb", "\t\n\r\\", "Heals.\n\tArgs: <n>", "plain"]
    )
    def it_reads_back_the_value_cell_rendered(self, value: str | None):
        assert uncell(cell(value)) == value

    def it_rejects_an_escape_cell_never_writes(self):
        with pytest.raises(KeyError):
            _ = uncell("a\\qb")


class DescribeListCell:
    def it_joins_with_spaces(self):
        assert list_cell(["cheat", "client_can_execute"]) == "cheat client_can_execute"

    def it_renders_no_items_as_an_empty_cell(self):
        assert list_cell([]) == ""

    @pytest.mark.parametrize("item", ["", "a b", "a\tb", "a\\b"])
    def it_rejects_an_item_that_would_not_round_trip(self, item: str):
        with pytest.raises(AssertionError):
            _ = list_cell(["ok", item])


class DescribeUnlistCell:
    @pytest.mark.parametrize("items", [[], ["cheat"], ["cheat", "client_can_execute", "flag_40"]])
    def it_reads_back_the_items_list_cell_rendered(self, items: list[str]):
        assert unlist_cell(list_cell(items)) == items


class DescribeLoadDocuments:
    def it_keys_each_document_by_its_dll_basename(self, tmp_path: Path):
        for name, doc in {"b.dll": [2], "Qt5Core.dll": [1]}.items():
            _ = (tmp_path / f"{name}.json").write_text(json.dumps(doc))
        paths = [str(tmp_path / "b.dll.json"), str(tmp_path / "Qt5Core.dll.json")]
        assert load_documents(paths, is_sequence) == {"b.dll": [2], "Qt5Core.dll": [1]}

    def it_rejects_a_path_not_named_for_a_document(self, tmp_path: Path):
        path = tmp_path / "b.dll"
        _ = path.write_text("[]")
        with pytest.raises(AssertionError):
            _ = load_documents([str(path)], is_sequence)

    def it_rejects_a_basename_given_twice(self, tmp_path: Path):
        (tmp_path / "x").mkdir()
        for path in (tmp_path / "a.dll.json", tmp_path / "x" / "a.dll.json"):
            _ = path.write_text("[]")
        with pytest.raises(AssertionError):
            _ = load_documents([str(tmp_path / "a.dll.json"), str(tmp_path / "x" / "a.dll.json")], is_sequence)

    def it_rejects_a_document_of_the_wrong_shape(self, tmp_path: Path):
        path = tmp_path / "a.dll.json"
        _ = path.write_text("{}")
        with pytest.raises(AssertionError):
            _ = load_documents([str(path)], is_sequence)


class DescribeIsStrSequence:
    @pytest.mark.parametrize(("value", "expected"), [([], True), (["a", "b"], True), ("ab", False), (["a", 1], False)])
    def it_accepts_only_a_list_of_strings(self, value: object, expected: bool):
        assert is_str_sequence(value) is expected
