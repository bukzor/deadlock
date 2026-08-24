import pytest

from .kv3 import load, loads

_HEADER = (
    "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d}"
    " format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"
)


class DescribeLoad:
    def it_loads_a_root_mapping_from_a_line_stream(self):
        lines = iter([_HEADER, "{\n", '\tfoo = "bar"\n', "\tn = 3\n", "}\n"])
        root = load(lines)
        assert root["foo"] == "bar"
        assert root["n"] == 3


class DescribeLoads:
    def it_loads_a_root_mapping_from_text(self):
        root = loads(_HEADER + '{\n\tfoo = "bar"\n\tn = 3\n}\n')
        assert root["foo"] == "bar"
        assert root["n"] == 3

    def it_rejects_a_non_mapping_root(self):
        with pytest.raises(AssertionError):
            _ = loads(_HEADER + "[ 1, 2, 3 ]\n")
