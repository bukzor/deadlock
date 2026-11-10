import pytest

from .dlls_check import COMMAND_ANCHORS, CONVAR_ANCHORS, QUEUE_DLLS, check_concommands, check_convars, check_strides
from .sparse import Table

HEADER = ["dll", "name", "flags", "help"]
CONVARS_HEADER = ["dll", "name", "type", "version", "default", "min", "max", "flags", "help"]


def _learned(*kinds: str | None) -> list[object]:
    return [{"stride": 64, "kind": kind, "entries": 2} for kind in kinds]


def _rows(**overrides: str) -> list[list[str]]:
    """One row per anchor (its required flags plus `defensive`) and per queue DLL."""
    rows = [[m, n, " ".join(sorted({*f, "defensive"})), "\\N"] for (m, n), f in COMMAND_ANCHORS.items()]
    rows += [[dll, "some_command", "", ""] for dll in QUEUE_DLLS]
    return [[r[0], r[1], overrides.get(r[1], r[2]), r[3]] for r in rows]


def _convar_rows(*extra: list[str]) -> list[list[str]]:
    """One row per anchor (its required flags plus `archive`) and per queue DLL, then `extra`."""
    rows = [
        [m, n, "bool", "0", "false", "\\N", "\\N", " ".join(sorted({*f, "archive"})), ""]
        for (m, n), f in CONVAR_ANCHORS.items()
    ]
    rows += [[dll, "some_convar", "int32", "0", "1", "\\N", "\\N", "", "\\N"] for dll in QUEUE_DLLS]
    return rows + list(extra)


def _convar(dll: str, name: str, flags: str) -> list[str]:
    return [dll, name, "float32", "0", "1.0", "\\N", "\\N", flags, ""]


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
            _ = check_concommands((["module", "name", "flags", "help"], _rows()))


LANE_SWAP = "citadel_lane_swap_available_duration_prematch"


class DescribeCheckConvars:
    def it_reports_the_anchor_rows_module_name_and_flags(self):
        rows = _convar_rows(_convar("server.dll", LANE_SWAP, "cheat replicated gamedll"))[::-1]
        table: Table = (CONVARS_HEADER, rows)
        assert check_convars(table) == (
            HEADER[:3],
            [["server.dll", LANE_SWAP, "cheat replicated gamedll"], ["server.dll", LANE_SWAP, "archive cheat replicated"]],
        )

    def it_checks_the_validation_anchor(self):
        assert CONVAR_ANCHORS == {("server.dll", LANE_SWAP): frozenset({"replicated", "cheat"})}

    def it_fails_on_a_missing_anchor(self):
        rows = [r for r in _convar_rows() if r[1] != LANE_SWAP]
        with pytest.raises(AssertionError):
            _ = check_convars((CONVARS_HEADER, rows))

    def it_fails_on_an_anchor_in_another_module(self):
        rows = [["client.dll" if r[1] == LANE_SWAP else r[0], *r[1:]] for r in _convar_rows()]
        with pytest.raises(AssertionError):
            _ = check_convars((CONVARS_HEADER, rows))

    @pytest.mark.parametrize("flags", ["cheat", "replicated", "", "cheat replicatedx"])
    def it_fails_when_any_copy_of_the_anchor_lacks_its_flags(self, flags: str):
        with pytest.raises(AssertionError):
            _ = check_convars((CONVARS_HEADER, _convar_rows(_convar("server.dll", LANE_SWAP, flags))))

    @pytest.mark.parametrize("dll", ["client.dll", "engine2.dll"])  # server's anchor covers server
    def it_fails_when_a_queue_dll_has_no_convars(self, dll: str):
        with pytest.raises(AssertionError):
            _ = check_convars((CONVARS_HEADER, [r for r in _convar_rows() if r[0] != dll]))

    def it_reads_the_flags_column_by_name(self):
        anchor = ["server.dll", LANE_SWAP, "cheat replicated", "0", "\\N", "\\N", "\\N", "", ""]  # in `type`'s place
        rows = [r for r in _convar_rows() if r[1] != LANE_SWAP] + [anchor]
        with pytest.raises(AssertionError):
            _ = check_convars((CONVARS_HEADER, rows))

    @pytest.mark.parametrize("header", [HEADER, [*CONVARS_HEADER[:-1], "helps"]])
    def it_rejects_another_header(self, header: list[str]):
        with pytest.raises(AssertionError):
            _ = check_convars((header, _convar_rows()))
