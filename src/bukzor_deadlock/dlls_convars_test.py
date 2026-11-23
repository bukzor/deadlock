import pytest

from dllscan import values
from dllscan.document import ConVar, ConVarsDocument, ConVarValue

from .dlls_convars import TYPES, is_convars_document, table, uncell_value, value_cell
from .dlls_tsv import uncell, unlist_cell
from .sparse import parse, render

HEADER = ["dll", "name", "type", "version", "default", "min", "max", "flags", "help"]


def _convar(
    name: str,
    type: str = "bool",
    default: ConVarValue | None = False,
    min: ConVarValue | None = None,
    max: ConVarValue | None = None,
    *,
    version: int = 0,
    help: str | None = "",
    flags: list[str] | None = None,
) -> ConVar:
    return ConVar(
        name=name, help=help, flags=flags or [], type=type, version=version, default=default, min=min, max=max
    )


SERVER = ConVarsDocument(
    dll="server.dll",
    convars=[
        _convar("zeta", "float32", 0.02, 0.0, 1.0, help="Seconds.\n\tSee also: x", flags=["replicated", "cheat"]),
        _convar("alpha", "string", "", version=3, help=None),
        _convar("zeta", "int32", None, -1, help="\\N"),
        _convar("mp_color", "color", [255, 0, 16, 255]),
    ],
)
CLIENT = ConVarsDocument(
    dll="client.dll",
    convars=[
        _convar("cl_vec", "vector3", [0.5, -0.0, 1e-07], flags=["flag_40"]),
        _convar("cl_name", "string", "tab\there\\N"),
        _convar("cl_on", "bool", True),
    ],
)
QT = ConVarsDocument(dll="Qt5Core.dll", convars=[])

VALUES: list[tuple[str, ConVarValue | None]] = [
    ("bool", True),
    ("bool", False),
    ("int8", -128),
    ("uint8", 255),
    ("int16", -32768),
    ("uint16", 65535),
    ("int32", -1),
    ("uint32", 4294967295),
    ("int64", -(2**63)),
    ("uint64", 2**64 - 1),
    ("float32", 0.02),
    ("float32", -0.0),
    ("float64", 0.1 + 0.2),
    ("string", ""),
    ("string", "\\N"),
    ("string", "a b\tc\n"),
    ("color", [255, 255, 255, 0]),
    ("vector2", [1.0, -2.5]),
    ("vector3", [0.0, 0.0, 0.0]),
    ("vector4", [1e-07, 3.4028234663852886e38, 0.0, -1.0]),
    ("qangle", [90.0, 0.0, -180.0]),
    ("vectorws", [0.0, 1.0, 2.0]),
    *((type, None) for type in TYPES),
]


class DescribeValueCell:
    @pytest.mark.parametrize(("type", "value"), VALUES)
    def it_reads_back_to_the_value_given_its_type(self, type: str, value: ConVarValue | None):
        text = value_cell(type, value)
        assert "\t" not in text and "\n" not in text, text
        read = uncell_value(type, text)
        assert (read, repr(read)) == (value, repr(value))

    @pytest.mark.parametrize(
        ("type", "value", "text"),
        [
            ("bool", True, "true"),
            ("bool", False, "false"),
            ("uint64", 2**64 - 1, "18446744073709551615"),
            ("float32", 0.02, "0.02"),
            ("float32", 1.0, "1.0"),
            ("string", "", ""),
            ("string", None, "\\N"),
            ("string", "\\N", "\\\\N"),
            ("color", [255, 0, 16, 255], "255 0 16 255"),
            ("vector3", [0.5, -0.0, 1e-07], "0.5 -0.0 1e-07"),
        ],
    )
    def it_spells_each_kind_plainly(self, type: str, value: ConVarValue | None, text: str):
        assert value_cell(type, value) == text

    @pytest.mark.parametrize(
        ("type", "value"),
        [("bool", 1), ("int32", True), ("int32", 1.0), ("float32", 1), ("string", 1), ("color", [1.0]), ("vector2", [1])],
    )
    def it_rejects_a_value_of_another_kind(self, type: str, value: ConVarValue):
        with pytest.raises(AssertionError):
            _ = value_cell(type, value)

    def it_rejects_an_unknown_type(self):
        with pytest.raises(KeyError):
            _ = value_cell("type_18", "00")


class DescribeTypes:
    def it_names_the_scanners_types_in_code_order(self):
        assert list(TYPES) == list(values.TYPES)


class DescribeTable:
    def it_renders_every_column_in_order(self):
        header, rows = table({"server.dll": SERVER})
        assert header == HEADER
        assert rows[0] == [
            "server.dll",
            "zeta",
            "float32",
            "0",
            "0.02",
            "0.0",
            "1.0",
            "replicated cheat",
            "Seconds.\\n\\tSee also: x",
        ]
        assert rows[1][:5] == ["server.dll", "alpha", "string", "3", ""]

    def it_keeps_null_and_empty_apart(self):
        rows = table({"server.dll": SERVER})[1]
        assert [row[8] for row in rows[1:3]] == ["\\N", "\\\\N"]
        assert [row[4] for row in rows[1:3]] == ["", "\\N"]

    def it_sorts_by_module_then_keeps_queue_order_and_duplicates(self):
        _, rows = table({"server.dll": SERVER, "Qt5Core.dll": QT, "client.dll": CLIENT})
        assert [(row[0], row[1]) for row in rows] == [
            ("client.dll", "cl_vec"),
            ("client.dll", "cl_name"),
            ("client.dll", "cl_on"),
            ("server.dll", "zeta"),
            ("server.dll", "alpha"),
            ("server.dll", "zeta"),
            ("server.dll", "mp_color"),
        ]

    def it_makes_a_rows_ordinal_within_its_module_its_queue_index(self):
        documents = {"server.dll": SERVER, "client.dll": CLIENT}
        _, rows = table(documents)
        for dll, document in documents.items():
            ordinal = [row[1] for row in rows if row[0] == document["dll"]]
            assert ordinal == [c["name"] for c in document["convars"]], dll

    def it_reads_back_to_the_documents_of_every_dll_with_a_queue(self):
        documents = {"server.dll": SERVER, "Qt5Core.dll": QT, "client.dll": CLIENT}
        read: dict[str, list[ConVar]] = {}
        for dll, name, type, version, default, min, max, flags, help in parse(render(table(documents)))[1]:
            convar = ConVar(
                name=str(uncell(name)),
                help=uncell(help),
                flags=unlist_cell(flags),
                type=type,
                version=int(version),
                default=uncell_value(type, default),
                min=uncell_value(type, min),
                max=uncell_value(type, max),
            )
            read.setdefault(dll, []).append(convar)
        assert read == {"client.dll": CLIENT["convars"], "server.dll": SERVER["convars"]}

    def it_rejects_a_document_for_another_dll(self):
        with pytest.raises(AssertionError):
            _ = table({"client.dll": SERVER})


def _plain(document: ConVarsDocument) -> dict[str, object]:
    return {"dll": document["dll"], "convars": [dict(c) for c in document["convars"]]}


def _with(**fields: object) -> dict[str, object]:
    return {"dll": "a.dll", "convars": [{**_convar("x"), **fields}]}


class DescribeIsConvarsDocument:
    @pytest.mark.parametrize("document", [SERVER, CLIENT, QT])
    def it_accepts_a_convars_document(self, document: ConVarsDocument):
        assert is_convars_document(_plain(document))

    @pytest.mark.parametrize(
        "value",
        [
            [],
            {"dll": "a.dll"},
            {"dll": 1, "convars": []},
            {"dll": "a.dll", "convars": {}},
            {"dll": "a.dll", "convars": [], "extra": 0},
            {"dll": "a.dll", "convars": [{k: v for k, v in _convar("x").items() if k != "version"}]},
            _with(extra=0),
            _with(name=1),
            _with(help=1),
            _with(flags="cheat"),
            _with(flags=[1]),
            _with(type=1),
            _with(type="type_18"),
            _with(version="0"),
            _with(version=True),
            _with(default=1),
            _with(min="x"),
            _with(max=[True]),
        ],
    )
    def it_rejects_anything_else(self, value: object):
        assert not is_convars_document(value)
