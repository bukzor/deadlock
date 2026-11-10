"""The registry readback check (``docs/dev/cvar-dump.kb/validation.md``): one
DLL's queue documents against tier0's registry after the DLL's ``Init``
(``dllscan registry``), so the queue decoding is checked against the engine,
not against our reading of the SDK. Run by ``data/dlls.check/registry.do``.

    bin/winpy dllscan registry DLL DIR... | python -m deadlock.registry_check CONVARS.json CONCOMMANDS.json

Every queue entry's name is in the registry. Each name declared once in its
queue must be registered as declared (6860, ``server`` and ``client``):

- ``flags``: the declaration's plus the DLL's ``PER_DLL_FLAG``, which
  registration adds; tier0's runtime ``STATE`` flags aside (one convar per
  DLL carries them after ``Init``'s stop, the summary counts them).
- ``help``: the declaration's, a null one as ``""``.
- A convar's ``type``, ``version``, ``default``, ``min`` and ``max``, as JSON,
  strictly (``0.0`` is not ``-0.0``).
- A ``reference`` declaration (has-default 0) registers no value of its own:
  the registry holds its type's zero value as the default, version -1, and its
  flags without ``SANITISED`` and without the per-DLL flag.

On success it prints a summary of the counts; any mismatch is an
``AssertionError`` naming each name and field.
"""

import json
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TypeGuard

import typed_json

from dllscan import values
from dllscan.document import ConCommand, ConCommandsDocument, ConVar, ConVarsDocument, ConVarValue, RegistryDocument
from dllscan.memory import Memory

from .dlls_concommands import is_concommands_document
from .dlls_convars import is_convars_document
from .types import is_str_mapping

PER_DLL_FLAG: Mapping[str, str] = {"server.dll": "gamedll", "client.dll": "clientdll"}
"""The flag ``ConVar_Register`` adds to each of the DLL's registrations."""
SANITISED = frozenset({"developmentonly", "defensive"})
"""What s2sdk's ``SanitiseConVarFlags`` adds to a declaration with none of
its listed flags; a ``reference`` declaration's registry flags lack it."""
STATE = frozenset({"initial_setvalue", "performing_callbacks"})
"""tier0's runtime state bits, not declaration flags."""

_NO_MEMORY = Memory(lambda addr, n: None)


def zero_value(type: str) -> ConVarValue | None:
    """The ``type``'s zero value as ``dllscan.values`` decodes it (``""`` for a string)."""
    return values.decode(_NO_MEMORY, type, 1, bytes(values.SIZE))


def _differing(want: Mapping[str, object], got: Mapping[str, object]) -> list[str]:
    return [field for field in want if json.dumps(want[field]) != json.dumps(got[field])]


def convar_mismatches(entry: ConVar, record: ConVar, per_dll: str) -> list[str]:
    """The fields in which the registry's ``record`` isn't the once-declared
    queue ``entry`` as registered, in document order."""
    reference = "reference" in entry["flags"]
    flags = set(entry["flags"]) - SANITISED if reference else {*entry["flags"], per_dll}
    want: dict[str, object] = {
        "help": entry["help"] or "",
        "flags": sorted(flags),
        "type": entry["type"],
        "version": -1 if reference else entry["version"],
        "default": zero_value(entry["type"]) if reference else entry["default"],
        "min": entry["min"],
        "max": entry["max"],
    }
    got: dict[str, object] = {**record, "flags": sorted(set(record["flags"]) - STATE)}
    return _differing(want, got)


def command_mismatches(entry: ConCommand, record: ConCommand, per_dll: str) -> list[str]:
    """``convar_mismatches`` for a command: its help and flags."""
    want = {"help": entry["help"] or "", "flags": sorted({*entry["flags"], per_dll})}
    return _differing(want, {**record, "flags": sorted(record["flags"])})


def _compare[R: (ConVar, ConCommand)](
    kind: str, queue: Sequence[R], records: Sequence[R], mismatches: Callable[[R, R], list[str]]
) -> tuple[list[R], list[tuple[str, str, list[str]]]]:
    """The once-declared entries of ``queue``, and each one's mismatching fields."""
    declared, registered = Counter(e["name"] for e in queue), Counter(r["name"] for r in records)
    twice = [name for name, n in registered.items() if n > 1]
    assert not twice, ("registered twice", kind, twice)
    missing = [name for name in declared if name not in registered]
    assert not missing, ("not in the registry", kind, missing)
    by_name = {r["name"]: r for r in records}
    once = [e for e in queue if declared[e["name"]] == 1]
    bad = [(kind, e["name"], fields) for e in once if (fields := mismatches(e, by_name[e["name"]]))]
    return once, bad


def check(registry: RegistryDocument, convars: ConVarsDocument, concommands: ConCommandsDocument) -> list[str]:
    """The summary lines of one DLL's check; ``AssertionError`` on any mismatch."""
    dll = registry["dll"]
    assert convars["dll"] == concommands["dll"] == dll, (dll, convars["dll"], concommands["dll"])
    assert dll in PER_DLL_FLAG, ("no per-DLL flag known", dll)
    per_dll = PER_DLL_FLAG[dll]
    once_convars, bad_convars = _compare(
        "convars", convars["convars"], registry["convars"], lambda e, r: convar_mismatches(e, r, per_dll)
    )
    once_commands, bad_commands = _compare(
        "concommands", concommands["concommands"], registry["concommands"], lambda e, r: command_mismatches(e, r, per_dll)
    )
    assert not (bad := bad_convars + bad_commands), ("registry mismatch", bad)
    stateful = sum(bool(STATE & set(r["flags"])) for r in registry["convars"])
    references = sum("reference" in e["flags"] for e in once_convars)
    counts = [
        (kind, len(queue), len(records), len(once))
        for kind, queue, records, once in (
            ("convars", convars["convars"], registry["convars"], once_convars),
            ("concommands", concommands["concommands"], registry["concommands"], once_commands),
        )
    ]
    return [
        f"{dll} registry: Init stopped by {registry['stopped_by']}; tier0 state flags on {stateful} convar",
        *(
            f"{dll} {kind}: queue {q}, registry {r}, once {o}{f' (reference {references})' if kind == 'convars' else ''}, all match"
            for kind, q, r, o in counts
        ),
    ]


def is_registry_document(value: object) -> TypeGuard[RegistryDocument]:
    return (
        is_str_mapping(value)
        and set(value) == {"dll", "stopped_by", "convars", "concommands"}
        and (value["stopped_by"] is None or isinstance(value["stopped_by"], str))
        and is_convars_document({"dll": value["dll"], "convars": value["convars"]})
        and is_concommands_document({"dll": value["dll"], "concommands": value["concommands"]})
    )


def main() -> None:
    match sys.argv[1:]:
        case [convars_path, concommands_path]:
            registry = typed_json.loads(sys.stdin.read())
            convars = typed_json.loads(Path(convars_path).read_text())
            concommands = typed_json.loads(Path(concommands_path).read_text())
        case argv:
            raise AssertionError("usage: registry_check CONVARS.json CONCOMMANDS.json <REGISTRY.json", argv)
    assert is_registry_document(registry), "not a registry document"
    assert is_convars_document(convars), convars_path
    assert is_concommands_document(concommands), concommands_path
    _ = sys.stdout.write("".join(line + "\n" for line in check(registry, convars, concommands)))


if __name__ == "__main__":
    main()
