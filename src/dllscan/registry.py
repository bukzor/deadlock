"""tier0's own cvar registry, read back after a DLL's `Init` has replayed the
DLL's queues into it (`docs/dev/cvar-dump.kb/capture-approach.kb/icvar-hook.md`).
A check on the queue scan, never a source: `deadlock.registry_check` compares
it with the DLL's `convars` and `concommands` documents.

`read_back` loads the DLL, `Connect`s tier0's cvar system, then `Connect`s and
`Init`s the DLL's app system (`APP_SYSTEMS`) through a factory of our own.
tier0 serves the interfaces it has; every other name the DLL asks for gets a
placeholder object of its own, whose every method returns 0 during `Connect`
and traps (`ud2`) from `Init` on. `Connect` uses some dependencies when they
are non-null, so a placeholder that trapped from the start would stop it;
`Init` replays the queues first, so its first use of a missing dependency
stops it with an `OSError` after the replay, not at a null read somewhere later.
`client`'s `Connect` faults on a placeholder's 0, and its `Init` still replays.

Everything native goes through `win32`. The rest (the placeholder block, the
registry's records) is pure over `Memory`, so WSL pytest drives it with fakes.
"""

import ctypes
import ntpath
from collections.abc import Callable, Mapping, Sequence
from typing import final

from . import flags, values, win32
from .document import ConCommand, ConVar, ConVarValue, RegistryDocument
from .memory import Memory
from .shape import ShapeError

APP_SYSTEMS: Mapping[str, str] = {
    "server.dll": "Source2ServerConfig001",
    "client.dll": "Source2ClientConfig001",
}
"""Lowercased basename → the app-system interface whose `Init` replays its queues."""

CVAR = "VEngineCvar007"
CONNECT, INIT = 0, 3
"""`IAppSystem` slots."""
GET_CONVAR_DATA, GET_CONCOMMAND_DATA = 41, 44
"""`ICvar` slots: data by access index, hidden entries included (6854, `icvar-hook.md`)."""
MAX_INDEX = 0xFFFF
"""An access index is a uint16; this one is the invalid ref's."""

SLOTS = 512
"""Placeholder vtable slots: more than any interface the DLLs ask for has."""
OBJECT = 128
OBJECTS = 256
_TRAPPED, _MODE, _STUB, _VTABLE = 0, 16, 64, 128
_POOL = _VTABLE + 8 * SLOTS
BLOCK = _POOL + OBJECT * OBJECTS
"""The placeholder block: the trapped `this` (u64 at 0) and the mode (u64 at
16; 0 returns, else traps), the one stub every slot runs, the shared vtable,
then the objects, each a vtable pointer and zeroed fields."""


def _stub(base: int) -> bytes:
    return b"".join((
        b"\x49\xbb" + base.to_bytes(8, "little"),  # mov r11, base
        b"\x49\x83\x7b\x10\x00",  # cmp qword [r11+16], 0     (the mode)
        b"\x75\x03",  # jne trap
        b"\x31\xc0\xc3",  # xor eax, eax; ret
        b"\x49\x89\x0b",  # trap: mov [r11], rcx    (this: which placeholder)
        b"\x0f\x0b",  # ud2
    ))  # fmt: skip


def block(base: int) -> bytes:
    """The placeholder block's bytes, to be written at `base`.

    >>> raw = block(0x10000)
    >>> len(raw) == BLOCK, raw[_POOL:_POOL + 8] == (0x10000 + _VTABLE).to_bytes(8, "little")
    (True, True)
    """
    stub = _stub(base).ljust(_VTABLE - _STUB, b"\xcc")
    vtable = (base + _STUB).to_bytes(8, "little") * SLOTS
    obj = (base + _VTABLE).to_bytes(8, "little").ljust(OBJECT, b"\0")
    return bytes(_STUB) + stub + vtable + obj * OBJECTS


class Placeholders:
    """The placeholder objects of the block at `base`, one per interface name."""

    def __init__(self, base: int) -> None:
        self.base: int = base
        self.mode: int = base + _MODE
        self.by_name: dict[str, int] = {}

    def make(self, name: str) -> int:
        """`name`'s placeholder object, the same one each time."""
        if name not in self.by_name:
            assert len(self.by_name) < OBJECTS, name
            self.by_name[name] = self.base + _POOL + OBJECT * len(self.by_name)
        return self.by_name[name]

    def tripped(self, mem: Memory) -> str | None:
        """The name whose placeholder trapped, or None if none did."""
        this = mem.u64(self.base + _TRAPPED)
        if not this:
            return None
        names = [name for name, obj in self.by_name.items() if obj == this]
        assert len(names) == 1, (hex(this), self.by_name)
        return names[0]


_ptr = ctypes.c_uint64


@final
class ConVarData(ctypes.LittleEndianStructure):
    """s2sdk `deadlock` 18139bdc96f1, `public/tier0/convar.h:1007-1025`: the
    fields up to the flags. Values are `CVValue_t*`, null for an absent min/max."""

    _fields_ = (
        ("m_pszName", _ptr),
        ("m_defaultValue", _ptr),
        ("m_minValue", _ptr),
        ("m_maxValue", _ptr),
        ("m_pszHelpString", _ptr),
        ("m_eVarType", ctypes.c_int16),
        ("m_Version", ctypes.c_int16),
        ("m_iTimesChanged", ctypes.c_uint32),
        ("m_nFlags", ctypes.c_uint64),
    )
    m_pszName: int = 0
    m_defaultValue: int = 0
    m_minValue: int = 0
    m_maxValue: int = 0
    m_pszHelpString: int = 0
    m_eVarType: int = 0
    m_Version: int = 0
    m_nFlags: int = 0


@final
class ConCommandData(ctypes.LittleEndianStructure):
    """`convar.h:518-520`: the fields up to the flags."""

    _fields_ = (("m_pszName", _ptr), ("m_pszHelpString", _ptr), ("m_nFlags", ctypes.c_uint64))
    m_pszName: int = 0
    m_pszHelpString: int = 0
    m_nFlags: int = 0


def convar_record(mem: Memory, addr: int) -> ConVar:
    """The `ConVarData` at `addr`, as a queue entry's `ConVar`; `ShapeError`
    with `addr` if it doesn't fit."""
    data = ConVarData.from_buffer_copy(_read(mem, addr, ctypes.sizeof(ConVarData)))
    try:
        type = values.type_name(data.m_eVarType)
        default, min, max = (_value(mem, type, p) for p in (data.m_defaultValue, data.m_minValue, data.m_maxValue))
        name, help = _text(mem, data.m_pszName, data.m_pszHelpString)
    except ShapeError as error:
        args: tuple[object, ...] = error.args
        what, *detail = args
        raise ShapeError(f"registry {what}", hex(addr), *detail) from None
    return ConVar(name=name, help=help, flags=flags.names(data.m_nFlags), type=type, version=data.m_Version,
                  default=default, min=min, max=max)  # fmt: skip


def command_record(mem: Memory, addr: int) -> ConCommand:
    """The `ConCommandData` at `addr`, as a queue entry's `ConCommand`."""
    data = ConCommandData.from_buffer_copy(_read(mem, addr, ctypes.sizeof(ConCommandData)))
    try:
        name, help = _text(mem, data.m_pszName, data.m_pszHelpString)
    except ShapeError as error:
        args: tuple[object, ...] = error.args
        what, *detail = args
        raise ShapeError(f"registry {what}", hex(addr), *detail) from None
    return ConCommand(name=name, help=help, flags=flags.names(data.m_nFlags))


def _read(mem: Memory, addr: int, size: int) -> bytes:
    raw = mem.read(addr, size)
    if raw is None:
        raise ShapeError("registry record unreadable", hex(addr))
    return raw


def _text(mem: Memory, name_p: int, help_p: int) -> tuple[str, str | None]:
    """A record's name and help (None if null): text anywhere in memory."""
    name = mem.cstr_in(name_p, 0, 1 << 64)
    if not name:
        raise ShapeError("name", hex(name_p))
    help = mem.cstr_in(help_p, 0, 1 << 64) if help_p else None
    if help_p and help is None:
        raise ShapeError("help", hex(help_p))
    return name, help


def _value(mem: Memory, type: str, pointer: int) -> ConVarValue | None:
    """The `CVValue_t*` `pointer`'s value. tier0 allocates a value its type's
    size, so only those bytes are read; null is an absent value."""
    if not pointer:
        return None
    raw = mem.read(pointer, values.TYPES[type])
    if raw is None:
        raise ShapeError("value unreadable", hex(pointer))
    return values.decode(mem, type, 1, raw.ljust(values.SIZE, b"\0"))


def walk(get: Callable[[int], int]) -> list[int]:
    """`get(index)` for access index 0 on, up to the first that is null or
    what the invalid index gets: `GetConVarData` returns null past the end,
    `GetConCommandData` a shared `<unknown>` record of tier0's (6860).

    >>> walk(lambda i: 5 if i == MAX_INDEX else [7, 8, 9, 5][i]), walk(lambda i: [7, 0][i % 2])
    ([7, 8, 9], [7])
    """
    end = get(MAX_INDEX)
    out: list[int] = []
    for index in range(MAX_INDEX):
        if (data := get(index)) in (0, end):
            return out
        out.append(data)
    raise AssertionError("no end", MAX_INDEX)


def _method(mem: Memory, obj: int, slot: int) -> int:
    vtable = mem.u64(obj)
    assert vtable, hex(obj)
    fn = mem.u64(vtable + 8 * slot)
    assert fn, (hex(obj), slot)
    return fn


def _call_until_stopped(fn: int, *args: int) -> None:
    """Call `fn`; a CPU exception stops it, and that is expected."""
    try:
        _ = win32.call(fn, *args)
    except OSError:
        pass


def read_back(dll: str, dirs: Sequence[str]) -> RegistryDocument:
    """Load `dll` (a Windows path; each of `dirs` searched), run its replay
    into tier0's registry, and read the registry back."""
    interface = APP_SYSTEMS[ntpath.basename(dll).lower()]
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    module = win32.load_library(dll)
    tier0_create = win32.proc_address(win32.module_handle("tier0.dll"), "CreateInterface")
    cvar = win32.call(tier0_create, CVAR.encode(), 0)
    assert cvar, CVAR
    _ = win32.call(_method(mem, cvar, CONNECT), cvar, tier0_create)

    base = win32.alloc_executable(BLOCK)
    win32.write(base, block(base))
    placeholders = Placeholders(base)

    def serve(name_p: int, rc: int) -> int:
        name = mem.cstr_in(name_p, 0, 1 << 64)
        assert name, hex(name_p)
        if rc:
            win32.write(rc, bytes(4))
        return win32.call(tier0_create, name_p, 0) or placeholders.make(name)

    app = win32.call(win32.proc_address(module, "CreateInterface"), interface.encode(), 0)
    assert app, interface
    _call_until_stopped(_method(mem, app, CONNECT), app, win32.callback(serve))
    win32.write(placeholders.mode, b"\1")
    _call_until_stopped(_method(mem, app, INIT), app)

    get_convar, get_command = (_method(mem, cvar, slot) for slot in (GET_CONVAR_DATA, GET_CONCOMMAND_DATA))
    return RegistryDocument(
        dll=ntpath.basename(dll),
        stopped_by=placeholders.tripped(mem),
        convars=[convar_record(mem, d) for d in walk(lambda i: win32.call(get_convar, cvar, i))],
        concommands=[command_record(mem, d) for d in walk(lambda i: win32.call(get_command, cvar, i))],
    )
