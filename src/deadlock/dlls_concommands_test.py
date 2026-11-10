import pytest

from dllscan.document import ConCommand, ConCommandsDocument

from .dlls_concommands import is_concommands_document, table
from .dlls_tsv import uncell, unlist_cell
from .sparse import parse, render

HEADER = ["dll", "name", "flags", "help"]


def _command(name: str, help: str | None = "", flags: list[str] | None = None) -> ConCommand:
    return ConCommand(name=name, help=help, flags=flags or [])


SERVER = ConCommandsDocument(
    dll="server.dll",
    concommands=[
        _command("zeta", "Heals the player.\n\tArguments: <health>", ["cheat", "client_can_execute"]),
        _command("alpha", None),
        _command("zeta", ""),
    ],
)
CLIENT = ConCommandsDocument(
    dll="client.dll", concommands=[_command("camerazoomin", None), _command("cl_crlf", "a\r\nb \\N", ["flag_40"])]
)
QT = ConCommandsDocument(dll="Qt5Core.dll", concommands=[])

NOT_DOCUMENTS: list[object] = [
    [],
    {"dll": "a.dll"},
    {"dll": 1, "concommands": []},
    {"dll": "a.dll", "concommands": {}},
    {"dll": "a.dll", "concommands": [{"name": "x", "help": None}]},
    {"dll": "a.dll", "concommands": [{"name": 1, "help": None, "flags": []}]},
    {"dll": "a.dll", "concommands": [{"name": "x", "help": 1, "flags": []}]},
    {"dll": "a.dll", "concommands": [{"name": "x", "help": None, "flags": "cheat"}]},
    {"dll": "a.dll", "concommands": [{"name": "x", "help": None, "flags": [1]}]},
    {"dll": "a.dll", "concommands": [], "extra": 0},
]


class DescribeTable:
    def it_renders_module_name_flags_and_escaped_help(self):
        assert table({"server.dll": SERVER})[1][0] == [
            "server.dll",
            "zeta",
            "cheat client_can_execute",
            "Heals the player.\\n\\tArguments: <health>",
        ]

    def it_keeps_null_help_and_empty_help_apart(self):
        assert [row[3] for row in table({"server.dll": SERVER})[1][1:]] == ["\\N", ""]

    def it_sorts_by_module_then_keeps_queue_order_and_duplicates(self):
        header, rows = table({"server.dll": SERVER, "Qt5Core.dll": QT, "client.dll": CLIENT})
        assert header == HEADER
        assert [(row[0], row[1]) for row in rows] == [
            ("client.dll", "camerazoomin"),
            ("client.dll", "cl_crlf"),
            ("server.dll", "zeta"),
            ("server.dll", "alpha"),
            ("server.dll", "zeta"),
        ]

    def it_makes_a_rows_ordinal_within_its_module_its_queue_index(self):
        documents = {"server.dll": SERVER, "client.dll": CLIENT}
        _, rows = table(documents)
        for dll, document in documents.items():
            ordinal = [row[1] for row in rows if row[0] == document["dll"]]
            assert ordinal == [c["name"] for c in document["concommands"]], dll

    def it_reads_back_to_the_documents_of_every_dll_with_a_queue(self):
        documents = {"server.dll": SERVER, "Qt5Core.dll": QT, "client.dll": CLIENT}
        read: dict[str, list[ConCommand]] = {}
        for dll, name, flags, help in parse(render(table(documents)))[1]:
            command = ConCommand(name=str(uncell(name)), help=uncell(help), flags=unlist_cell(flags))
            read.setdefault(dll, []).append(command)
        assert read == {"client.dll": CLIENT["concommands"], "server.dll": SERVER["concommands"]}

    def it_rejects_a_document_for_another_dll(self):
        with pytest.raises(AssertionError):
            _ = table({"client.dll": SERVER})

    def it_rejects_a_document_whose_module_differs_from_the_listed_basename_in_case(self):
        with pytest.raises(AssertionError):
            _ = table({"Server.dll": SERVER})


class DescribeIsConcommandsDocument:
    def it_accepts_a_concommands_document(self):
        assert is_concommands_document({"dll": "server.dll", "concommands": [dict(c) for c in SERVER["concommands"]]})

    @pytest.mark.parametrize("value", NOT_DOCUMENTS)
    def it_rejects_anything_else(self, value: object):
        assert not is_concommands_document(value)
