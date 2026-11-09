import pytest

from .dlls_check import COMMAND_ANCHORS, QUEUE_DLLS, check_concommands, check_strides
from .sparse import Table

HEADER = ["module", "name", "flags", "help"]


def _learned(*kinds: str | None) -> list[object]:
    return [{"stride": 64, "kind": kind, "entries": 2} for kind in kinds]


def _rows(**overrides: str) -> list[list[str]]:
    """One row per anchor (its required flags plus `defensive`) and per queue DLL."""
    rows = [[m, n, " ".join(sorted({*f, "defensive"})), "\\N"] for (m, n), f in COMMAND_ANCHORS.items()]
    rows += [[dll, "some_command", "", ""] for dll in QUEUE_DLLS]
    return [[r[0], r[1], overrides.get(r[1], r[2]), r[3]] for r in rows]


class DescribeCheckStrides:
    def it_passes_when_each_kind_labels_one_queue(self):
        check_strides(_learned("concommands", "convars"))

    @pytest.mark.parametrize(
        "kinds",
        [
            ("concommands", None),
            (None, None),
            ("concommands", "concommands"),
            ("concommands", "convars", "convars"),
            ("concommands", "convars", None),
        ],
    )
    def it_fails_unless_each_kind_labels_exactly_one(self, kinds: tuple[str | None, ...]):
        with pytest.raises(AssertionError):
            check_strides(_learned(*kinds))

    @pytest.mark.parametrize("learned", [{}, [["concommands"]]])
    def it_rejects_another_shape(self, learned: object):
        with pytest.raises(AssertionError):
            check_strides(learned)


class DescribeCheckConcommands:
    def it_reports_the_anchor_rows_without_help(self):
        header, rows = check_concommands((HEADER, _rows()[::-1]))
        assert header == HEADER[:3]
        assert rows[-1] == ["server.dll", "bot_kick_all", "defensive"]
        assert [(r[0], r[1]) for r in rows] == list(COMMAND_ANCHORS)[::-1]

    def it_reports_a_duplicate_anchor_twice(self):
        table: Table = (HEADER, _rows() + [["tier0.dll", "find", "release", ""]])
        assert [r[1] for r in check_concommands(table)[1]].count("find") == 2

    def it_checks_the_validation_anchors(self):
        assert COMMAND_ANCHORS == {
            ("server.dll", "bot_kick_all"): frozenset(),
            ("server.dll", "citadel_bot_kick"): frozenset({"developmentonly"}),
            ("tier0.dll", "find"): frozenset(),
        }
        assert QUEUE_DLLS == ("client.dll", "engine2.dll", "server.dll")

    @pytest.mark.parametrize("anchor", sorted(COMMAND_ANCHORS))
    def it_fails_on_a_missing_anchor(self, anchor: tuple[str, str]):
        rows = [r for r in _rows() if (r[0], r[1]) != anchor]
        with pytest.raises(AssertionError):
            _ = check_concommands((HEADER, rows))

    def it_fails_on_an_anchor_in_another_module(self):
        rows = [["client.dll" if r[1] == "find" else r[0], *r[1:]] for r in _rows()]
        with pytest.raises(AssertionError):
            _ = check_concommands((HEADER, rows))

    def it_fails_when_any_copy_of_an_anchor_lacks_its_flags(self):
        table: Table = (HEADER, _rows() + [["server.dll", "citadel_bot_kick", "cheat", ""]])
        with pytest.raises(AssertionError):
            _ = check_concommands(table)
        with pytest.raises(AssertionError):
            _ = check_concommands((HEADER, _rows(citadel_bot_kick="developmentonlyx")))

    @pytest.mark.parametrize("dll", ["client.dll", "engine2.dll"])  # server's anchors cover server
    def it_fails_when_a_queue_dll_has_no_commands(self, dll: str):
        with pytest.raises(AssertionError):
            _ = check_concommands((HEADER, [r for r in _rows() if r[0] != dll]))

    def it_rejects_another_header(self):
        with pytest.raises(AssertionError):
            _ = check_concommands((["dll", "name", "flags", "help"], _rows()))
