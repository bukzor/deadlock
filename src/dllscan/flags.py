"""FCVAR flag bits → names, as DumpSource2 prints them.

Bits are the `FCVAR_*` defines of s2sdk (`deadlock` branch, 18139bdc96f1,
`public/tier0/convar.h:174-231`). Names and order are DumpSource2's
(00759ce86fa6, `GetFlagNames` and `g_flagMap` in
`src/main/dumpers/concommands/concommands.cpp`), so our output diffs cleanly
against its `convars.txt`. A name is the define lowercased with `FCVAR_` dropped,
except `FCVAR_NOT_CONNECTED`, which DumpSource2 spells `notconnected`.

A set bit with no name is written `flag_<bit index>` (not its mask), after every
named bit, as DumpSource2 does:

>>> names(1 << 35 | 1 << 32 | 1 << 14)
('cheat', 'defensive', 'flag_35')
"""

from collections.abc import Mapping

BY_BIT: Mapping[int, str] = {
    0: "linked_concommand",
    1: "developmentonly",
    2: "gamedll",
    3: "clientdll",
    4: "hidden",
    5: "protected",
    6: "sponly",
    7: "archive",
    8: "notify",
    9: "userinfo",
    10: "reference",
    11: "unlogged",
    12: "initial_setvalue",
    13: "replicated",
    14: "cheat",
    15: "per_user",
    16: "demo",
    17: "dontrecord",
    18: "performing_callbacks",
    19: "release",
    20: "menubar_item",
    21: "commandline_enforced",
    22: "notconnected",
    23: "vconsole_fuzzy_matching",
    24: "server_can_execute",
    25: "client_can_execute",
    26: "server_cannot_query",
    27: "vconsole_set_focus",
    28: "clientcmd_can_execute",
    29: "execute_per_tick",
    30: "snapshot_ignored",
    32: "defensive",
    33: "execute_immediately",
    34: "gameinfo_cannot_override",
    36: "vconsole_no_change_notify",
    37: "enum_value",
}
"""Bit index → name, ascending."""


def names(flags: int) -> tuple[str, ...]:
    """The names of the bits set in a 64-bit flag word: named bits in bit order,
    then unnamed ones as `flag_<n>` in bit order."""
    assert 0 <= flags < 1 << 64, flags
    bits = [bit for bit in range(64) if flags >> bit & 1]
    named = [BY_BIT[bit] for bit in bits if bit in BY_BIT]
    unnamed = [f"flag_{bit}" for bit in bits if bit not in BY_BIT]
    return (*named, *unnamed)
