"""The ``cvarlist`` oracle (``docs/dev/cvar-dump.kb/validation.md``): one side's
capture of the engine's own listing (``bin/cvarlist-capture``,
``deadlock.cvarlist``) against the store's declarations
(``data/dlls/{convars,concommands}.tsv``). The only check that catches a DLL
whose queue the scan missed outright. Run by ``data/dlls.check/cvarlist.do``.

    python -m deadlock.cvarlist_check SIDE.log GAMEINFO.gi CONVARS.tsv CONCOMMANDS.tsv

Each rule is what 6860's two captures showed
(``docs/dev/game-runtime.kb/cvarlist-capture.md``):

- Every listed name has a ``listable`` declaration in the store.
- A DLL is loaded if a listed name is declared listably by it alone
  (``loaded_dlls``). Every listable declaration of a loaded DLL is listed.
- A listed name prints the flags of the declarations that explain it
  (``explaining``), as registered (``PER_DLL_FLAG`` added), through ``WORDS``,
  less ``NEVER_PRINTED``.
- Its help is their one non-empty help, under ``printed_help``'s rule.
- Its value is ``cmd`` for a command. A convar's prints its default
  (``render``): ``gameinfo.gi``'s ``ConVars`` override if it has one
  (``overrides``), else the store's. A name in ``differences`` prints its
  current value instead, which the table repeats beside that default.

On success it prints a summary of counts; any mismatch is an
``AssertionError`` naming each name.
"""

import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

import vdf

from dllscan.document import ConVarValue

from . import cvarlist, dlls_tsv
from .dlls_convars import TYPES, uncell_value
from .registry_check import PER_DLL_FLAG
from .sparse import parse as parse_table
from .types import is_sequence, is_str_mapping

UNLISTED = frozenset({"developmentonly", "hidden"})
"""A declaration with one of these flags is never listed."""
NEVER_PRINTED = frozenset(
    {
        "client_can_execute",
        "commandline_enforced",
        "defensive",
        "execute_immediately",
        "gameinfo_cannot_override",
        "reference",
        "snapshot_ignored",
    }
)
WORDS: Mapping[str, str] = {
    "archive": "a",
    "replicated": "rep",
    "notify": "nf",
    "dontrecord": "norecord",
    "userinfo": "user",
    "protected": "prot",
    "linked_concommand": "linked",
    "server_cannot_query": "server_cant_query",
    "vconsole_fuzzy_matching": "vconsole_fuzzy",
    "gamedll": "sv",
    "clientdll": "cl",
}
"""The listing's abbreviation of a store flag; any other prints as itself."""


class Declaration(NamedTuple):
    dll: str
    name: str
    flags: frozenset[str]
    help: str | None
    type: str | None
    """``None`` for a command."""
    default: ConVarValue | None


def declarations(convars: str, concommands: str) -> list[Declaration]:
    """The rows of ``convars.tsv`` and ``concommands.tsv``, given their text."""
    out: list[Declaration] = []
    for text, kind in ((convars, "convar"), (concommands, "concommand")):
        header, rows = parse_table(text)
        for row in rows:
            cell = dict(zip(header, row, strict=True))
            type_ = cell["type"] if kind == "convar" else None
            out.append(
                Declaration(
                    cell["dll"],
                    cell["name"],
                    frozenset(dlls_tsv.unlist_cell(cell["flags"])),
                    dlls_tsv.uncell(cell["help"]),
                    type_,
                    None if type_ is None else uncell_value(type_, cell["default"]),
                )
            )
    return out


def overrides(gameinfo: str) -> dict[str, str]:
    """``gameinfo.gi``'s ``ConVars`` defaults by name: a plain value, or a
    block's ``default`` (a block's ``min``, ``max`` and ``version`` don't print)."""
    root = vdf.loads(gameinfo)
    assert is_str_mapping(root), type(root)
    info = root["GameInfo"]
    assert is_str_mapping(info), type(info)
    block = info["ConVars"]
    assert is_str_mapping(block), type(block)
    out: dict[str, str] = {}
    for name, value in block.items():
        if isinstance(value := value.get("default") if is_str_mapping(value) else value, str):
            out[name] = value
    return out


def listable(d: Declaration) -> bool:
    """Not ``UNLISTED``, and not the ``-`` half of a ``+``/``-`` command."""
    return not d.flags & UNLISTED and not (d.type is None and d.name.startswith("-"))


def loaded_dlls(listed: Iterable[str], by_name: Mapping[str, Sequence[Declaration]]) -> set[str]:
    """The DLLs some listed name proves loaded: those it is listably declared by alone."""
    out: set[str] = set()
    for name in listed:
        dlls = {d.dll for d in by_name.get(name, ()) if listable(d)}
        if len(dlls) == 1:
            out |= dlls
    return out


def explaining(decls: Sequence[Declaration], loaded: set[str]) -> list[Declaration]:
    """Of a listed name's ``decls``, the listable ones of loaded DLLs; if no
    loaded DLL declares it, every listable one (none proven loaded, any may be)."""
    candidates = [d for d in decls if listable(d)]
    return [d for d in candidates if d.dll in loaded] or candidates


def printed_words(decls: Iterable[Declaration]) -> set[str]:
    words: set[str] = set()
    for d in decls:
        registered = d.flags | {PER_DLL_FLAG[d.dll]} if d.dll in PER_DLL_FLAG else d.flags
        words |= {WORDS.get(flag, flag) for flag in registered - NEVER_PRINTED}
    return words


def printed_help(decls: Iterable[Declaration]) -> str | None:
    """The one help the declarations carry, ``\\n`` and ``\\t`` as spaces and
    ``"`` as ``'``; ``""`` if none has one; ``None`` if they disagree."""
    helps = {d.help.replace("\n", " ").replace("\t", " ").replace('"', "'") for d in decls if d.help}
    return "" if not helps else helps.pop() if len(helps) == 1 else None


def _float(value: object) -> str:
    assert isinstance(value, float), value
    return repr(value).removesuffix(".0")


def render(type_: str, value: ConVarValue) -> str:
    """``value`` as the listing prints a ``type_`` value."""
    match TYPES[type_]:
        case "bool":
            return "true" if value else "false"
        case "int":
            return str(value)
        case "float":
            return _float(value)
        case "str":
            assert isinstance(value, str), value
            return value or "0"
        case "floats":
            assert is_sequence(value), value
            return " ".join(map(_float, value))
        case "ints":
            assert is_sequence(value), value
            return " ".join(map(str, value[:3]))


def parse_override(type_: str, text: str) -> ConVarValue:
    """A ``gameinfo.gi`` value as a ``type_`` value."""
    match TYPES[type_]:
        case "bool":
            return {"0": False, "1": True, "false": False, "true": True}[text]
        case "int":
            return int(text)
        case "float":
            return float(text)
        case "str":
            return text
        case "floats":
            return [float(item) for item in text.split()]
        case "ints":
            return [int(item) for item in text.split()]


def expected_value(decls: Sequence[Declaration], gameinfo: Mapping[str, str]) -> tuple[str, str] | None:
    """What a listed name explained by ``decls`` prints at its default, and
    that default's source; ``None`` if they disagree on kind, type or default."""
    if len({(d.type, repr(d.default)) for d in decls}) != 1:
        return None
    d = decls[0]
    if d.type is None:
        return "cmd", "command"
    if d.name in gameinfo:
        return render(d.type, parse_override(d.type, gameinfo[d.name])), "gameinfo.gi"
    assert d.default is not None, ("a listed reference declaration: no rule known", d)
    return render(d.type, d.default), "store default"


def _fails(rule: str, names: Sequence[str]) -> None:
    assert not names, (rule, list(names))


def check(label: str, capture: cvarlist.Capture, store: Sequence[Declaration], gameinfo: Mapping[str, str]) -> list[str]:
    """The summary lines of one side's check; ``AssertionError`` on any mismatch."""
    listed = {e.name: e for e in capture.entries}
    assert len(listed) == len(capture.entries) == capture.total, (len(listed), len(capture.entries), capture.total)
    by_name: defaultdict[str, list[Declaration]] = defaultdict(list)
    for d in store:
        by_name[d.name].append(d)
    _fails("listed, no listable declaration", [n for n in listed if not any(map(listable, by_name.get(n, ())))])
    loaded = loaded_dlls(listed, by_name)
    in_loaded = [d for d in store if d.dll in loaded]
    _fails("listable in a loaded DLL, unlisted", sorted({d.name for d in in_loaded if listable(d) and d.name not in listed}))
    explain = {n: explaining(by_name[n], loaded) for n in listed}
    _fails("flags", [n for n, e in listed.items() if set(e.flags) != printed_words(explain[n])])
    _fails("help", [n for n, e in listed.items() if e.help != printed_help(explain[n])])
    sources = _check_values(listed, explain, gameinfo, capture.differences)
    omitted = Counter(
        "developmentonly or hidden" if d.flags & UNLISTED else "'-' command" for d in in_loaded if not listable(d)
    )
    kinds = Counter("commands" if listed[n].value == "cmd" else "convars" for n in listed)
    return [
        f"{label}: listed {len(listed)} = its total line ({kinds['convars']} convars, {kinds['commands']} commands)",
        f"{label}: {len(loaded)} DLLs loaded, by names only they declare: {' '.join(sorted(loaded))}",
        f"{label}: their {len(in_loaded)} declarations: every listable one listed; omitted "
        + ", ".join(f"{kind} {n}" for kind, n in sorted(omitted.items())),
        f"{label}: flags and help agree on all {len(listed)}; values: "
        + ", ".join(f"{source} {n}" for source, n in sorted(sources.items())),
    ]


def _check_values(
    listed: Mapping[str, cvarlist.Entry],
    explain: Mapping[str, Sequence[Declaration]],
    gameinfo: Mapping[str, str],
    differences: Sequence[cvarlist.Difference],
) -> Counter[str]:
    """Each listed value against its expected one; the count of each source."""
    changed = {d.name: d for d in differences}
    _fails("in differences, unlisted", [n for n in changed if n not in listed])
    expected: dict[str, tuple[str, str]] = {}
    for name in listed:
        if (value := expected_value(explain[name], gameinfo)) is not None:
            expected[name] = value
    _fails("declarations disagree on kind, type or default", [n for n in listed if n not in expected])
    sources: Counter[str] = Counter()
    wrong: list[str] = []
    for name, entry in listed.items():
        want, source = expected[name]
        if name in changed:
            source, ok = "differences", (changed[name].value, changed[name].default) == (entry.value, want)
        else:
            ok = entry.value == want
        sources[source] += 1
        wrong += [] if ok else [name]
    _fails("value", wrong)
    return sources


def main() -> None:
    match sys.argv[1:]:
        case [log, gameinfo, convars, concommands]:
            capture = cvarlist.parse(Path(log).read_text(encoding="utf-8-sig"))
            store = declarations(Path(convars).read_text(), Path(concommands).read_text())
            gi = overrides(Path(gameinfo).read_text(encoding="utf-8"))
        case argv:
            raise AssertionError("usage: cvarlist_check SIDE.log GAMEINFO.gi CONVARS.tsv CONCOMMANDS.tsv", argv)
    label = Path(log).stem
    _ = sys.stdout.write("".join(line + "\n" for line in check(label, capture, store, gi)))


if __name__ == "__main__":
    main()
