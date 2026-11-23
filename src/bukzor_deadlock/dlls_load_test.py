import pytest

from dllscan.document import LoadDocument, LoadExcluded, LoadFailed, LoadOk

from .dlls_load import is_load_document, ok, table
from .dlls_tsv import uncell, unlist_cell
from .sparse import parse, render

DOCUMENTS: dict[str, LoadDocument] = {
    "server.dll": LoadOk(outcome="ok", modules=["server.dll", "tier0.dll"]),
    "vfx_dx11.dll": LoadFailed(outcome="failed", error="LoadLibraryExW: 126"),
    "helpsystem.dll": LoadExcluded(outcome="excluded", reason="LoadLibrary hangs"),
    "Qt5Core.dll": LoadOk(outcome="ok", modules=[]),
}


class DescribeTable:
    def it_has_one_row_per_dll_sorted_by_basename_with_its_outcomes_detail(self):
        assert table(DOCUMENTS) == (
            ["dll", "outcome", "detail"],
            [
                ["Qt5Core.dll", "ok", ""],
                ["helpsystem.dll", "excluded", "LoadLibrary hangs"],
                ["server.dll", "ok", "server.dll tier0.dll"],
                ["vfx_dx11.dll", "failed", "LoadLibraryExW: 126"],
            ],
        )

    def it_escapes_an_error_or_reason(self):
        documents: dict[str, LoadDocument] = {
            "a.dll": LoadFailed(outcome="failed", error="x\ty"),
            "b.dll": LoadExcluded(outcome="excluded", reason="p\nq"),
        }
        assert table(documents)[1] == [["a.dll", "failed", "x\\ty"], ["b.dll", "excluded", "p\\nq"]]


    def it_reads_back_to_the_documents(self):
        read: dict[str, LoadDocument] = {}
        for dll, outcome, detail in parse(render(table(DOCUMENTS)))[1]:
            match outcome:
                case "ok":
                    read[dll] = LoadOk(outcome="ok", modules=unlist_cell(detail))
                case "failed":
                    read[dll] = LoadFailed(outcome="failed", error=str(uncell(detail)))
                case _:
                    read[dll] = LoadExcluded(outcome="excluded", reason=str(uncell(detail)))
        assert read == DOCUMENTS


class DescribeOk:
    def it_lists_the_dlls_that_loaded_sorted(self):
        assert ok(DOCUMENTS) == ["Qt5Core.dll", "server.dll"]


class DescribeIsLoadDocument:
    @pytest.mark.parametrize("value", [dict(d) for d in DOCUMENTS.values()])
    def it_accepts_each_outcome(self, value: object):
        assert is_load_document(value)

    @pytest.mark.parametrize(
        "value",
        [
            [],
            {"outcome": "ok"},
            {"outcome": "ok", "modules": "a.dll"},
            {"outcome": "ok", "modules": [1]},
            {"outcome": "ok", "error": "x"},
            {"outcome": "failed", "error": None},
            {"outcome": "failed", "error": "x", "modules": []},
            {"outcome": "excluded", "reason": 1},
            {"outcome": "excluded", "reason": "x", "error": "y"},
            {"outcome": "skipped", "reason": "x"},
        ],
    )
    def it_rejects_anything_else(self, value: object):
        assert not is_load_document(value)
