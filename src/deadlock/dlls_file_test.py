import pytest

from dllscan.document import FileDocument

from .dlls_file import is_file_document, table
from .sparse import parse, render

SHA = "ab" * 32


class DescribeTable:
    def it_has_one_row_per_dll_sorted_by_basename(self):
        documents = {
            "server.dll": FileDocument(size=20, sha256=SHA),
            "Qt5Core.dll": FileDocument(size=10, sha256="cd" * 32),
        }
        assert table(documents) == (
            ["dll", "size", "sha256"],
            [["Qt5Core.dll", "10", "cd" * 32], ["server.dll", "20", SHA]],
        )


    def it_reads_back_to_the_documents(self):
        documents = {"a.dll": FileDocument(size=0, sha256=SHA), "b.dll": FileDocument(size=2**40, sha256=SHA)}
        rows = parse(render(table(documents)))[1]
        assert {dll: FileDocument(size=int(size), sha256=sha) for dll, size, sha in rows} == documents


class DescribeIsFileDocument:
    def it_accepts_a_file_document(self):
        assert is_file_document({"size": 1, "sha256": SHA})

    @pytest.mark.parametrize(
        "value",
        [
            [],
            {"size": "1", "sha256": SHA},
            {"size": True, "sha256": SHA},
            {"size": 1, "sha256": 1},
            {"size": 1},
            {"size": 1, "sha256": SHA, "extra": 0},
        ],
    )
    def it_rejects_anything_else(self, value: object):
        assert not is_file_document(value)
