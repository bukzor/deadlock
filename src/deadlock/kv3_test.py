from pathlib import Path

import pytest

from .kv3 import load

_HEADER = (
    "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d}"
    " format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"
)


def _write_kv3(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "data.kv3"
    p.write_text(_HEADER + body)
    return p


class DescribeLoad:
    def it_loads_a_text_kv3_root_mapping(self, tmp_path: Path):
        path = _write_kv3(tmp_path, '{\n\tfoo = "bar"\n\tn = 3\n}\n')
        root = load(path)
        assert root["foo"] == "bar"
        assert root["n"] == 3

    def it_rejects_a_non_mapping_root(self, tmp_path: Path):
        path = _write_kv3(tmp_path, "[ 1, 2, 3 ]\n")
        with pytest.raises(AssertionError):
            load(path)
