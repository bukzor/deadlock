import pytest

from .cvarlist import Difference, Entry, parse

P = "11/10 12:10:34 [Console] "
"""A ``[Console]`` message line's prefix."""

LISTING = [
    '11/10 12:10:34     bind scancode87 "exec storm_diag" // US English key name "KP_PLUS"',
    P + "cvar list",
    "--------------",
    P + "_record                                                                          : cmd              : cheat, norecord, release         : Record a demo incrementally.",
    P + "axis                                                                             : cmd              : sv, cheat                        : Draw an axis  Arguments:  x y z pitch yaw roll <lifetime = 10.0> <r g b a> ",
    P + f"{'unflagged':<80} : {'0':<16} : {'':<32} : ",
    P + "adsp_debug                                                                       : 0                : a                                : ",
    P + "bot_mimic                                                                        : 0                : sv, cl, rep, cheat, release      : Allows bots to mimic player",
    P + "voice_device_override                                                            : Microphone (ATH-M50xSTS-USB) : a                                : Which audio input device to use",
    P + "--------------",
    "6 total convars/concommands",
]
"""6860's client log, cut to five rows (one widened by its value), plus one
without flags (``%-80s : %-16s : %-32s : %s``)."""

WIDTHS = (49, 322, 8, 32, 128)


def _table(*rows: tuple[str, ...]) -> list[str]:
    """A ``differences`` table as ``%-*s`` prints it, columns ``WIDTHS`` wide."""
    def line(cells: tuple[str, ...]) -> str:
        return P + " ".join(f"{cell:<{w}}" for cell, w in zip(cells[:-1], WIDTHS)) + " " + cells[-1]

    return [line(("name", "value", "default", "flags", "help text")), P + " ".join("_" * w for w in WIDTHS)] + [
        line(row) for row in rows
    ]


DIFFERENCES = _table(
    ("hud_fastswitch", "1", "0", "client archive"),
    ("name", "o.O worky", "unnamed", "archive per_user"),
    ("voice_threshold", "-38.85", "-120", "client archive", "decibel threshold for how loud"),
)
AFTER = ["11/10 12:10:34 [HostStateManager] CHostStateMgr::QueueNewRequest( Quitting, 2 )"]


def _log(*parts: list[str]) -> str:
    return "\r\n".join(line for part in parts for line in part) + "\r\n"


class DescribeParse:
    def it_reads_each_row_of_the_listing(self):
        capture = parse(_log(LISTING, [P + "no results"], AFTER))
        assert capture.entries == [
            Entry("_record", "cmd", ("cheat", "norecord", "release"), "Record a demo incrementally."),
            Entry("axis", "cmd", ("sv", "cheat"), "Draw an axis  Arguments:  x y z pitch yaw roll <lifetime = 10.0> <r g b a> "),
            Entry("unflagged", "0", (), ""),
            Entry("adsp_debug", "0", ("a",), ""),
            Entry("bot_mimic", "0", ("sv", "cl", "rep", "cheat", "release"), "Allows bots to mimic player"),
            Entry("voice_device_override", "Microphone (ATH-M50xSTS-USB)", ("a",), "Which audio input device to use"),
        ]

    def it_reads_the_total(self):
        assert parse(_log(LISTING, [P + "no results"], AFTER)).total == 6

    def it_reads_no_differences(self):
        assert parse(_log(LISTING, [P + "no results"], AFTER)).differences == []

    def it_reads_the_differences_table(self):
        assert parse(_log(LISTING, DIFFERENCES, AFTER)).differences == [
            Difference("hud_fastswitch", "1", "0", ("client", "archive"), ""),
            Difference("name", "o.O worky", "unnamed", ("archive", "per_user"), ""),
            Difference("voice_threshold", "-38.85", "-120", ("client", "archive"), "decibel threshold for how loud"),
        ]

    def it_rejects_a_differences_cell_wider_than_its_column(self):
        wide = DIFFERENCES[:2] + [P + f"{'v':<49} {'1':<322} {'1 0.5 0.25':<8} archive"]
        with pytest.raises(AssertionError, match="overflows"):
            _ = parse(_log(LISTING, wide, AFTER))

    @pytest.mark.parametrize("line", [AFTER[0], P + "Interpreting bind command as:"])
    def it_rejects_a_foreign_line_inside_the_listing(self, line: str):
        interleaved = [*LISTING[:4], line, *LISTING[4:]]
        with pytest.raises(AssertionError, match="not a listing row"):
            _ = parse(_log(interleaved, [P + "no results"]))

    def it_rejects_a_log_without_the_listing(self):
        with pytest.raises(AssertionError, match="no cvar list"):
            _ = parse(_log(AFTER))
