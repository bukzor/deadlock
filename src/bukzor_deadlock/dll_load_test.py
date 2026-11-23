import json
from pathlib import Path

import pytest

from dllscan import facets
from dllscan.document import LoadExcluded

from . import dll_load

HANGS = {"helpsystem.dll", "assetpreview.dll", "propertyeditor.dll", "toolframework2.dll"}


class DescribeExcluded:
    def it_lists_exactly_the_dlls_whose_load_hangs(self):
        assert set(dll_load.EXCLUDED) == HANGS

    def it_records_the_reason(self):
        assert dll_load.excluded("helpsystem.dll") == {
            "outcome": "excluded",
            "reason": dll_load.EXCLUDED["helpsystem.dll"],
        }

    def it_gives_every_exclusion_a_reason(self):
        assert all(dll_load.EXCLUDED.values()), dll_load.EXCLUDED

    def it_keeps_the_declared_key_order(self):
        doc = dll_load.excluded("helpsystem.dll")
        assert doc is not None
        assert list(doc) == list(LoadExcluded.__annotations__)

    def it_is_none_for_a_dll_that_loads(self):
        assert dll_load.excluded("server.dll") is None

    def it_is_none_for_a_dll_whose_load_fails(self):
        assert dll_load.excluded("vfx_dx11.dll") is None


class DescribeRequireOk:
    def it_accepts_an_ok_load(self):
        dll_load.require_ok({"outcome": "ok", "modules": ["server.dll"]})

    def it_fails_naming_a_failed_load(self):
        with pytest.raises(AssertionError, match="'failed'"):
            dll_load.require_ok({"outcome": "failed", "error": "LoadLibraryExW: 126"})

    def it_fails_naming_an_excluded_load(self):
        with pytest.raises(AssertionError, match="'excluded'"):
            dll_load.require_ok({"outcome": "excluded", "reason": "hangs"})

    def it_fails_on_a_document_without_an_outcome(self):
        with pytest.raises(AssertionError, match="outcome"):
            dll_load.require_ok({"modules": []})


class DescribeMain:
    def it_prints_an_excluded_dlls_record(self, capsys: pytest.CaptureFixture[str]):
        dll_load.main(["dll_load", "excluded", "helpsystem.dll"])
        reason = json.dumps(dll_load.EXCLUDED["helpsystem.dll"])
        assert capsys.readouterr().out == (
            f'{{\n  "outcome": "excluded",\n  "reason": {reason}\n}}\n'
        )

    def it_formats_like_the_scanners_documents(
        self, capsys: pytest.CaptureFixture[str]
    ):
        dll_load.main(["dll_load", "excluded", "helpsystem.dll"])
        assert capsys.readouterr().out == facets.dumps(
            dll_load.excluded("helpsystem.dll")
        )

    def it_prints_nothing_for_a_dll_to_load(self, capsys: pytest.CaptureFixture[str]):
        dll_load.main(["dll_load", "excluded", "server.dll"])
        assert capsys.readouterr().out == ""

    def it_passes_an_ok_load_document(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ):
        doc = tmp_path / "server.dll.json"
        _ = doc.write_text('{"outcome": "ok", "modules": ["server.dll"]}\n')
        dll_load.main(["dll_load", "ok", str(doc)])
        assert capsys.readouterr().out == ""

    def it_fails_on_a_failed_load_document_naming_the_outcome(self, tmp_path: Path):
        doc = tmp_path / "vfx_dx11.dll.json"
        _ = doc.write_text('{"outcome": "failed", "error": "LoadLibraryExW: 126"}\n')
        with pytest.raises(AssertionError, match="'failed'"):
            dll_load.main(["dll_load", "ok", str(doc)])

    def it_rejects_an_unknown_subcommand(self):
        with pytest.raises(AssertionError, match="bogus"):
            dll_load.main(["dll_load", "bogus", "server.dll"])
