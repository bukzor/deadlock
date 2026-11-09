"""The reg-list queue entries' layout, as s2sdk's `public/tier0/convar.h` declares
it (`deadlock` 18139bdc96f1, lines cited per struct), for a 64-bit target: one
`ctypes` struct per C struct, read line for line against the header.

Fields take their natural alignment, as the compiler gives them, so ctypes
inserts the same padding and the header's fields are the whole list. No pack is
needed for the values at 31, 47 and 63: `ConVarValueInfo_t` declares them
`uint8[16]` ("to prevent align issues"), not `CVValue_t`. The padding holds
stale stack bytes. Pointers are `uint64`: their targets are not read through here.
A derived struct (`: CVarCreationBase_t`) lists its base's fields first, as C++
lays them out. The fields `entries` reads are also annotated, for pyright, which
can't see `_fields_`; ctypes replaces each placeholder value with the field.

Sizes and offsets agree with the queues: `convar_h_test` checks each entry's
size against `reglist.STRIDES` and each field's offset against
`docs/dev/convar-dump.kb/registration-flow.md`'s registry fit (6860).

>>> entry = ConVarRegList_Entry_t.from_buffer_copy(bytes(range(160)))
>>> info = entry.m_Info.m_valueInfo
>>> info.m_bHasDefault, info.m_defaultValue[0], info.m_eVarType == 120 | 121 << 8
(28, 31, True)
"""

import ctypes
from typing import cast, final

_ptr = ctypes.c_uint64
_u8 = ctypes.c_uint8

CVValue_t = _u8 * 16
"""`union CVValue_t` (`:94-155`) as raw bytes: `values` decodes them by type."""


@final
class CVarCreationBase_t(ctypes.LittleEndianStructure):
    """`:157-168`; both creation structs lead with it."""

    _fields_ = (
        ("m_pszName", _ptr),
        ("m_pszHelpString", _ptr),
        ("m_nFlags", ctypes.c_uint64),
    )
    m_pszName: int = 0
    m_pszHelpString: int = 0
    m_nFlags: int = 0


@final
class CompletionCallbackInfo_t(ctypes.LittleEndianStructure):
    """`:449-487`."""

    _fields_ = (
        ("m_fnCompletionCallback", _ptr),  # union with m_pCommandCompletionCallback
        ("m_bIsInterface", _u8),
    )


@final
class ConVarValueInfo_t(ctypes.LittleEndianStructure):
    """`:630-728`. `m_eVarType` indexes tier0's type table (`values.TYPES`), not
    s2sdk's stale `EConVarType`."""

    _fields_ = (
        ("m_Version", ctypes.c_int32),
        ("m_bHasDefault", _u8),
        ("m_bHasMin", _u8),
        ("m_bHasMax", _u8),
        ("m_defaultValue", CVValue_t),
        ("m_minValue", CVValue_t),
        ("m_maxValue", CVValue_t),
        ("m_fnProviderCallBack", _ptr),
        ("m_fnCallBack", _ptr),
        ("m_fnProviderFilterCallBack", _ptr),
        ("m_fnFilterCallBack", _ptr),
        ("m_fnGetEnumInfoHandle", _ptr),
        ("m_eVarType", ctypes.c_int16),
        ("m_CompletionCallBack", CompletionCallbackInfo_t),
    )
    m_Version: int = 0
    m_bHasDefault: int = 0
    m_bHasMin: int = 0
    m_bHasMax: int = 0
    m_defaultValue: ctypes.Array[ctypes.c_uint8] = CVValue_t()
    m_minValue: ctypes.Array[ctypes.c_uint8] = CVValue_t()
    m_maxValue: ctypes.Array[ctypes.c_uint8] = CVValue_t()
    m_eVarType: int = 0


@final
class ConVarCreation_t(ctypes.LittleEndianStructure):
    """`:730-733`."""

    _fields_ = (*CVarCreationBase_t._fields_, ("m_valueInfo", ConVarValueInfo_t))
    m_valueInfo: ConVarValueInfo_t = ConVarValueInfo_t()


@final
class ConVarRegList_Entry_t(ctypes.LittleEndianStructure):
    """`ConVarRegList::Entry_t` (`:1596-1602`)."""

    _fields_ = (
        ("m_Info", ConVarCreation_t),
        ("m_pConVar", _ptr),
        ("m_pConVarData", _ptr),
    )
    m_Info: ConVarCreation_t = ConVarCreation_t()


@final
class ConCommandCallbackInfo_t(ctypes.LittleEndianStructure):
    """`:382-447`."""

    _fields_ = (
        ("m_fnCommandCallback", _ptr),  # union with the void, contextless and interface forms
        ("m_bIsInterface", _u8, 1),
        ("m_bIsVoidCallback", _u8, 1),
        ("m_bIsContextLess", _u8, 1),
    )


@final
class ConCommandCreation_t(ctypes.LittleEndianStructure):
    """`:489-493`."""

    _fields_ = (
        *CVarCreationBase_t._fields_,
        ("m_CBInfo", ConCommandCallbackInfo_t),
        ("m_CompletionCBInfo", CompletionCallbackInfo_t),
    )


@final
class ConCommandRegList_Entry_t(ctypes.LittleEndianStructure):
    """`ConCommandRegList::Entry_t` (`:1566-1570`)."""

    _fields_ = (
        ("m_Info", ConCommandCreation_t),
        ("m_Command", _ptr),
    )
    m_Info: ConCommandCreation_t = ConCommandCreation_t()


def offset_of(struct: type[ctypes.Structure], path: str) -> int:
    """The byte offset in `struct` of the field named by the dotted `path`
    (`"m_Info.m_nFlags"`): `offsetof`, typed for pyright."""
    *outer, last = path.split(".")
    root = obj = struct()
    for name in outer:
        obj = cast(object, getattr(obj, name))
        assert isinstance(obj, ctypes.Structure), (path, obj)
    at = cast(object, getattr(cast(object, getattr(type(obj), last)), "offset"))
    assert isinstance(at, int), (path, at)
    return ctypes.addressof(obj) - ctypes.addressof(root) + at
