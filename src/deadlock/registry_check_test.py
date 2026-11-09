import pytest

from dllscan.document import ConCommand, ConCommandsDocument, ConVar, ConVarsDocument, ConVarValue, RegistryDocument

from .dlls_convars import is_convars_document
from .registry_check import check, command_mismatches, convar_mismatches


def _with(entry: ConVar, **fields: object) -> ConVar:
    """`entry` with `fields` replaced, checked to still be a `ConVar`."""
    document = {"module": "", "convars": [{**entry, **fields}]}
    assert is_convars_document(document), fields
    return document["convars"][0]


def _convar(name: str = "cv", *flags: str, **fields: object) -> ConVar:
    base = ConVar(name=name, help=None, flags=list(flags), type="float32", version=0, default=0.5, min=0.0, max=None)
    return _with(base, **fields)


def _registered(entry: ConVar, *flags: str, **fields: object) -> ConVar:
    """`entry` as the registry holds it: help "" for null, `flags` added."""
    return _with(entry, **{"help": entry["help"] or "", "flags": [*entry["flags"], *flags], **fields})


REFERENCE = _convar("ref", "developmentonly", "reference", "defensive", default=None, min=None, type="vector2")
REFERENCE_RECORD = _with(REFERENCE, help="", flags=["reference"], default=[0.0, 0.0], version=-1)


def _command(name: str = "cc", *flags: str, help: str | None = "does it") -> ConCommand:
    return ConCommand(name=name, help=help, flags=list(flags))


def _documents(
    convars: list[ConVar],
    records: list[ConVar],
    commands: list[ConCommand],
    command_records: list[ConCommand],
    module: str = "server.dll",
) -> tuple[RegistryDocument, ConVarsDocument, ConCommandsDocument]:
    return (
        RegistryDocument(module=module, stopped_by="IPulseSystem_001", convars=records, concommands=command_records),
        ConVarsDocument(module=module, convars=convars),
        ConCommandsDocument(module=module, concommands=commands),
    )


class DescribeConvarMismatches:
    def it_passes_the_registered_form(self):
        entry = _convar("cv", "cheat", help="text")
        assert convar_mismatches(entry, _registered(entry, "gamedll"), "gamedll") == []

    def it_reads_null_help_as_empty(self):
        entry = _convar()
        assert convar_mismatches(entry, _registered(entry, "gamedll", help=None), "gamedll") == ["help"]

    @pytest.mark.parametrize(
        ("field", "value"),
        [("help", "other"), ("type", "float64"), ("version", 1), ("default", 0.25), ("min", None), ("max", 1.0)],
    )
    def it_names_each_field_that_differs(self, field: str, value: ConVarValue | None):
        entry = _convar()
        assert convar_mismatches(entry, _registered(entry, "gamedll", **{field: value}), "gamedll") == [field]

    def it_compares_values_strictly(self):
        entry = _convar(default=0.0)
        assert convar_mismatches(entry, _registered(entry, "gamedll", default=-0.0), "gamedll") == ["default"]

    def it_requires_the_per_dll_flag(self):
        entry = _convar()
        assert convar_mismatches(entry, _registered(entry), "gamedll") == ["flags"]

    def it_accepts_a_per_dll_flag_already_declared(self):
        entry = _convar("cv", "gamedll")
        assert convar_mismatches(entry, _registered(entry), "gamedll") == []

    def it_rejects_any_other_added_flag(self):
        entry = _convar()
        assert convar_mismatches(entry, _registered(entry, "gamedll", "cheat"), "gamedll") == ["flags"]

    def it_rejects_a_dropped_flag(self):
        entry = _convar("cv", "cheat")
        record = _registered(entry, "gamedll", flags=["gamedll"])
        assert convar_mismatches(entry, record, "gamedll") == ["flags"]

    def it_ignores_tier0s_runtime_state_flags(self):
        entry = _convar()
        record = _registered(entry, "gamedll", "initial_setvalue", "performing_callbacks")
        assert convar_mismatches(entry, record, "gamedll") == []

    class WhenTheDeclarationIsAReference:
        def it_expects_the_zero_value_version_minus_one_and_no_added_flags(self):
            assert convar_mismatches(REFERENCE, REFERENCE_RECORD, "gamedll") == []

        @pytest.mark.parametrize(
            ("field", "value"),
            [("default", [0.0, 1.0]), ("default", None), ("version", 0), ("min", [0.0, 0.0])],
        )
        def it_names_a_value_that_breaks_the_rule(self, field: str, value: ConVarValue | None):
            record = _with(REFERENCE_RECORD, **{field: value})
            assert convar_mismatches(REFERENCE, record, "gamedll") == [field]

        @pytest.mark.parametrize(
            "flags",
            [["reference", "gamedll"], ["reference", "developmentonly"], ["developmentonly", "reference", "defensive"]],
        )
        def it_expects_the_flags_without_the_sanitisers_pair(self, flags: list[str]):
            record = _with(REFERENCE_RECORD, flags=flags)
            assert convar_mismatches(REFERENCE, record, "gamedll") == ["flags"]


class DescribeCommandMismatches:
    def it_passes_the_registered_form(self):
        assert command_mismatches(_command(), _command("cc", "gamedll"), "gamedll") == []

    def it_reads_null_help_as_empty(self):
        assert command_mismatches(_command(help=None), _command("cc", "gamedll", help=""), "gamedll") == []

    @pytest.mark.parametrize(
        ("record", "fields"),
        [
            (_command("cc"), ["flags"]),
            (_command("cc", "gamedll", "cheat"), ["flags"]),
            (_command("cc", "gamedll", "initial_setvalue"), ["flags"]),
            (_command("cc", "gamedll", help="other"), ["help"]),
        ],
    )
    def it_names_each_field_that_differs(self, record: ConCommand, fields: list[str]):
        assert command_mismatches(_command(), record, "gamedll") == fields


class DescribeCheck:
    def it_summarises_the_counts(self):
        twice = _convar("twice")
        convars = [_convar("a"), twice, REFERENCE, _convar("twice", default=9.0)]
        records = [_registered(_convar("a"), "gamedll", "performing_callbacks"), _registered(twice), REFERENCE_RECORD]
        commands = [_command("x"), _command("y", "gamedll")]
        assert check(*_documents(convars, records, commands, [_command("x", "gamedll"), _command("y", "gamedll")])) == [
            "server.dll registry: Init stopped by IPulseSystem_001; tier0 state flags on 1 convar",
            "server.dll convars: queue 4, registry 3, once 2 (reference 1), all match",
            "server.dll concommands: queue 2, registry 2, once 2, all match",
        ]

    def it_fails_naming_each_mismatch(self):
        convars = [_convar("a"), _convar("b"), _convar("c")]
        records = [_registered(_convar("a"), "gamedll", version=2), _registered(_convar("b"), "gamedll"), _registered(_convar("c"))]
        with pytest.raises(AssertionError) as raised:
            _ = check(*_documents(convars, records, [_command("x")], [_command("x")]))
        assert raised.value.args[0] == (
            "registry mismatch",
            [("convars", "a", ["version"]), ("convars", "c", ["flags"]), ("concommands", "x", ["flags"])],
        )

    @pytest.mark.parametrize("kind", ["convars", "concommands"])
    def it_fails_naming_queue_names_missing_from_the_registry(self, kind: str):
        twice = _convar("twice")
        convars, records = [_convar("a"), twice, twice], [_registered(_convar("a"), "gamedll")]
        commands, command_records = [_command("x"), _command("y")], [_command("x", "gamedll")]
        if kind == "convars":
            commands = command_records = []
        else:
            records = [*records, _registered(twice, "gamedll")]
        with pytest.raises(AssertionError) as raised:
            _ = check(*_documents(convars, records, commands, command_records))
        missing = {"convars": ["twice"], "concommands": ["y"]}[kind]
        assert raised.value.args[0] == ("not in the registry", kind, missing)

    def it_rejects_a_name_the_registry_holds_twice(self):
        records = [_registered(_convar("a"), "gamedll")] * 2
        with pytest.raises(AssertionError, match="twice"):
            _ = check(*_documents([_convar("a")], records, [], []))

    def it_rejects_documents_of_different_modules(self):
        registry, _, concommands = _documents([], [], [], [])
        with pytest.raises(AssertionError):
            _ = check(registry, ConVarsDocument(module="client.dll", convars=[]), concommands)

    def it_rejects_a_dll_without_a_per_dll_flag(self):
        with pytest.raises(AssertionError, match="engine2"):
            _ = check(*_documents([], [], [], [], module="engine2.dll"))
