import pytest

from dllscan.document import ConVarValue

from .cvarlist import Capture, Difference, Entry
from .cvarlist_check import (
    Declaration,
    check,
    declarations,
    explaining,
    loaded_dlls,
    overrides,
    printed_help,
    parse_override,
    printed_words,
    render,
)

CONVARS_TSV = (
    "dll\tname\ttype\tversion\tdefault\tmin\tmax\tflags\thelp\n"
    "server.dll\tbot_mimic\tint32\t0\t0\t\\N\t\\N\treplicated cheat release\tAllows bots to mimic player\n"
    "client.dll\tbot_mimic\tint32\t0\t0\t\\N\t\\N\treplicated cheat\t\\N\n"
    "engine2.dll\tvoice_threshold\tfloat32\t0\t-120.0\t\\N\t\\N\tclientdll archive\tdecibel threshold\\tfor\\n\"loud\"\n"
)
CONCOMMANDS_TSV = "dll\tname\tflags\thelp\nclient.dll\t-chatwheel\tlinked_concommand\t\n"
"""6860's rows, one help given a tab, a newline and quotes."""

GAMEINFO = """"GameInfo"
{
	ConVars
	{
		"rate"
		{
			"min"		"98304"
			"default"	"786432"
		}
		"sv_maxunlag"	"0.500"	// a comment
		"voice_always_sample_mic"
		{
			"version"	"2"
		}
	}
}
"""
"""6860's ``gameinfo.gi``, cut down; one block without a default."""


def _decl(dll: str, name: str, *flags: str, help: str | None = None, type: str | None = "int32", default: ConVarValue | None = 0):
    return Declaration(dll, name, frozenset(flags), help, type, default)


def _cmd(dll: str, name: str, *flags: str, help: str | None = None):
    return _decl(dll, name, *flags, help=help, type=None, default=None)


class DescribeDeclarations:
    def it_reads_both_tables(self):
        assert declarations(CONVARS_TSV, CONCOMMANDS_TSV) == [
            _decl("server.dll", "bot_mimic", "replicated", "cheat", "release", help="Allows bots to mimic player"),
            _decl("client.dll", "bot_mimic", "replicated", "cheat"),
            _decl("engine2.dll", "voice_threshold", "clientdll", "archive", help='decibel threshold\tfor\n"loud"', type="float32", default=-120.0),
            _cmd("client.dll", "-chatwheel", "linked_concommand", help=""),
        ]


class DescribeOverrides:
    def it_reads_plain_values_and_block_defaults(self):
        assert overrides(GAMEINFO) == {"rate": "786432", "sv_maxunlag": "0.500"}


class DescribeRender:
    @pytest.mark.parametrize(
        ("type", "value", "printed"),
        [
            ("bool", False, "false"),
            ("int32", -1, "-1"),
            ("float32", 0.0, "0"),
            ("float32", 0.8, "0.8"),
            ("float32", 1e-05, "1e-05"),
            ("float32", 1000000.0, "1000000"),
            ("string", "unnamed", "unnamed"),
            ("string", "", "0"),
            ("vector3", [1.0, 0.5, 0.25], "1 0.5 0.25"),
            ("color", [128, 128, 128, 255], "128 128 128"),
        ],
    )
    def it_prints_as_the_listing_does(self, type: str, value: ConVarValue, printed: str):
        assert render(type, value) == printed


BY_NAME = {
    "only_server": [_decl("server.dll", "only_server")],
    "shared": [_decl("rendersystemdx11.dll", "shared"), _decl("rendersystemempty.dll", "shared")],
    "dev_elsewhere": [_decl("tier0.dll", "dev_elsewhere"), _decl("host.dll", "dev_elsewhere", "developmentonly")],
}


class DescribeParseOverride:
    @pytest.mark.parametrize(
        ("type", "text", "value"),
        [
            ("bool", "0", False),
            ("bool", "true", True),
            ("int32", "786432", 786432),
            ("float32", "0.500", 0.5),
            ("string", "Default_Mix", "Default_Mix"),
            ("vector3", "1 0 0", [1.0, 0.0, 0.0]),
            ("color", "255 0 16 255", [255, 0, 16, 255]),
        ],
    )
    def it_reads_a_gameinfo_value_by_type(self, type: str, text: str, value: ConVarValue):
        assert parse_override(type, text) == value


class DescribeLoadedDlls:
    def it_takes_a_dll_that_alone_declares_a_listed_name(self):
        assert loaded_dlls(["only_server"], BY_NAME) == {"server.dll"}

    def it_takes_no_dll_from_a_name_two_declare(self):
        assert loaded_dlls(["shared"], BY_NAME) == set()

    def it_ignores_unlistable_declarations(self):
        assert loaded_dlls(["dev_elsewhere"], BY_NAME) == {"tier0.dll"}


class DescribeExplaining:
    def it_keeps_the_listable_declarations_of_loaded_dlls(self):
        decls = [_decl("server.dll", "n"), _decl("client.dll", "n"), _decl("tier0.dll", "n", "hidden")]
        assert explaining(decls, {"server.dll", "tier0.dll"}) == decls[:1]

    def it_keeps_every_listable_one_if_no_loaded_dll_declares_it(self):
        decls = [_decl("rendersystemdx11.dll", "n"), _decl("rendersystemempty.dll", "n"), _decl("x.dll", "n", "hidden")]
        assert explaining(decls, {"server.dll"}) == decls[:2]


class DescribePrintedWords:
    def it_abbreviates(self):
        assert printed_words([_decl("tier0.dll", "n", "archive", "replicated", "cheat")]) == {"a", "rep", "cheat"}

    def it_adds_the_per_dll_flag_registration_adds(self):
        assert printed_words([_decl("server.dll", "n"), _decl("client.dll", "n")]) == {"sv", "cl"}

    def it_leaves_out_flags_never_printed(self):
        assert printed_words([_decl("tier0.dll", "n", "defensive", "reference", "release")]) == {"release"}


class DescribePrintedHelp:
    def it_normalizes_whitespace_and_quotes(self):
        assert printed_help([_decl("x.dll", "n", help='a\tb\n"c"')]) == "a b 'c'"

    def it_takes_the_one_non_empty_help(self):
        assert printed_help([_decl("x.dll", "n"), _decl("y.dll", "n", help="h"), _decl("z.dll", "n", help="")]) == "h"

    def it_prints_none_as_empty(self):
        assert printed_help([_decl("x.dll", "n")]) == ""

    def it_has_none_for_two_helps(self):
        assert printed_help([_decl("x.dll", "n", help="h"), _decl("y.dll", "n", help="i")]) is None


STORE = [
    _decl("server.dll", "sv_cheats", "replicated", help="Allow cheats", type="bool", default=False),
    _decl("server.dll", "rate", type="int32", default=80000),
    _cmd("server.dll", "kill", "cheat"),
    _cmd("server.dll", "-attack"),
    _decl("server.dll", "dev_only", "developmentonly"),
    _decl("engine2.dll", "name", "archive", type="string", default="unnamed"),
    _decl("client.dll", "cl_only"),
]
LISTED = [
    Entry("kill", "cmd", ("sv", "cheat"), ""),
    Entry("name", "unnamed", ("a",), ""),
    Entry("rate", "786432", ("sv",), ""),
    Entry("sv_cheats", "false", ("sv", "rep"), "Allow cheats"),
]


def _check(entries: list[Entry] = LISTED, differences: list[Difference] | None = None, total: int | None = None):
    capture = Capture(entries, len(entries) if total is None else total, differences or [])
    return check("server", capture, STORE, {"rate": "786432"})


def _replace(name: str, **fields: str | tuple[str, ...]) -> list[Entry]:
    return [e._replace(**fields) if e.name == name else e for e in LISTED]


class DescribeCheck:
    def it_summarizes_a_matching_capture(self):
        assert _check() == [
            "server: listed 4 = its total line (3 convars, 1 commands)",
            "server: 2 DLLs loaded, by names only they declare: engine2.dll server.dll",
            "server: their 6 declarations: every listable one listed; omitted '-' command 1, developmentonly or hidden 1",
            "server: flags and help agree on all 4; values: command 1, gameinfo.gi 1, store default 2",
        ]

    def it_counts_values_from_differences(self):
        changed = Difference("name", "o.O worky", "unnamed", ("archive",), "")
        assert _check(_replace("name", value="o.O worky"), [changed])[-1].endswith(
            "command 1, differences 1, gameinfo.gi 1, store default 1"
        )

    def it_fails_a_total_other_than_the_rows(self):
        with pytest.raises(AssertionError, match="4, 4, 5"):
            _ = _check(total=5)

    @pytest.mark.parametrize(
        ("entries", "differences", "rule", "names"),
        [
            ([*LISTED, Entry("unknown", "0", (), "")], [], "listed, no listable declaration", ["unknown"]),
            ([*LISTED, Entry("dev_only", "0", (), "")], [], "listed, no listable declaration", ["dev_only"]),
            (LISTED[1:], [], "listable in a loaded DLL, unlisted", ["kill"]),
            (_replace("kill", flags=("cheat",)), [], "flags", ["kill"]),
            (_replace("name", flags=("archive",)), [], "flags", ["name"]),
            (_replace("sv_cheats", help="Allow cheats "), [], "help", ["sv_cheats"]),
            (_replace("sv_cheats", value="0"), [], "value", ["sv_cheats"]),
            (_replace("rate", value="80000"), [], "value", ["rate"]),
            (_replace("kill", value="0"), [], "value", ["kill"]),
            (LISTED, [Difference("name", "unnamed", "x", (), "")], "value", ["name"]),
            (LISTED, [Difference("name", "x", "unnamed", (), "")], "value", ["name"]),
            (LISTED, [Difference("gone", "1", "0", (), "")], "in differences, unlisted", ["gone"]),
        ],
    )
    def it_fails_a_broken_rule_naming_the_names(
        self, entries: list[Entry], differences: list[Difference], rule: str, names: list[str]
    ):
        with pytest.raises(AssertionError) as raised:
            _ = _check(entries, differences)
        assert raised.value.args[0] == (rule, names)

    def it_fails_declarations_that_disagree_on_the_default(self):
        store = [*STORE, _decl("engine2.dll", "rate", type="int32", default=1)]
        capture = Capture(LISTED, 4, [])
        with pytest.raises(AssertionError) as raised:
            _ = check("client", capture, store, {})
        assert raised.value.args[0] == ("declarations disagree on kind, type or default", ["rate"])
