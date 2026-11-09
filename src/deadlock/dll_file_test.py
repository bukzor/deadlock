from pathlib import Path

import pytest

from dllscan import facets
from dllscan.document import FileDocument

from . import dll_file

ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


class DescribeDocument:
    def it_records_the_size_and_sha256(self):
        assert dll_file.document(b"abc") == {"size": 3, "sha256": ABC_SHA256}

    def it_keeps_the_declared_key_order(self):
        assert list(dll_file.document(b"abc")) == list(FileDocument.__annotations__)


class DescribeMain:
    def it_prints_the_dlls_document(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ):
        dll = tmp_path / "server.dll"
        _ = dll.write_bytes(b"abc")
        dll_file.main(["dll_file", str(dll)])
        assert capsys.readouterr().out == (
            f'{{\n  "size": 3,\n  "sha256": "{ABC_SHA256}"\n}}\n'
        )

    def it_formats_like_the_scanners_documents(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ):
        dll = tmp_path / "server.dll"
        _ = dll.write_bytes(b"abc")
        dll_file.main(["dll_file", str(dll)])
        out = capsys.readouterr().out
        assert out == facets.dumps(dll_file.document(b"abc"))
