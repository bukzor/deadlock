# How a cvar gets registered

Per s2sdk `deadlock` (`public/tier0/convar.h`, `tier0_perproject/convar.cpp`),
consistent with DumpSource2's comments; build 6848.

1. **Static initializer builds it.** Each `ConVar`/`ConCommand` is a global whose
   constructor fills a `ConVarCreation_t` (`m_pszName`, `m_pszHelpString`,
   `m_nFlags`, then `ConVarValueInfo_t`: type, has-default/min/max, the values,
   callbacks, enum handle) or `ConCommandCreation_t`. The values are written by
   code, so no static table in the DLL holds them.
2. **It's queued per DLL.** `SetupConVar` → `ConVarRegList::AddToList`
   (`convar.cpp:202`) appends `Entry_t{m_Info, m_pConVar, m_pConVarData}` to a
   linked list of 100-entry blocks headed by the unexported `s_pRoot`. Each DLL
   statically links its own copy of this code ("tier0_perproject"), so each has
   its own queue — tier0 too (24 commands and 3 convars on 6851). Loading the
   DLL is enough to fill it.
3. **`ConVar_Register` replays it into `g_pCVar`** (`convar.cpp:256`): commands
   first, then convars, block by block from `s_pRoot` (newest, the only partial
   one) back, entries in order, each as
   `g_pCVar->RegisterConVar(entry.m_Info, s_nCVarFlag, entry.m_pConVar, entry.m_pConVarData)`
   or `g_pCVar->RegisterConCommand(entry.m_Info, s_nCVarFlag)`, each writing its
   result back through the entry (`*pCvarData`, `*m_Command`). An invalid
   returned ref is `Plat_FatalError`. The blocks stay; only `UnregisterAll`
   frees them (`convar.cpp:180`).
4. **`ConVar_Register` runs in `Init`, not `Connect`**: `server.dll`'s and
   `client.dll`'s `Connect` make no cvar-system call, their `Init` replays the
   whole queue (6851, `capture-approach.kb/icvar-hook.md`), despite DumpSource2's
   comment "Connecting frees the convar queues" (`appframework.cpp:163`).
   `g_pCVar` is whatever the factory returned for `VEngineCvar007`; the real
   implementation lives in `tier0.dll`, which exports `CreateInterface`.

Retail hiding is a flag, not absence: `developmentonly` entries are registered
like any other (DumpSource2 dumps 3055 such convar lines for 6848), and
`ICvar::StripDevelopmentFlags` exists. `ConVar_Register`'s per-DLL flag adds
`gamedll` (0x4, server) or `clientdll` (client) to every registration but a
`reference` declaration's (6860, `validation.md`, "Registry readback").

Entry sizes on 6848 and 6851, measured from the queues: `ConVarRegList::Entry_t`
160 bytes, `ConCommandRegList::Entry_t` 64 (`capture-approach.kb/queue-shape-scan.md`).

## The convar entry's layout (6860)

Both entries, as s2sdk's `convar.h` declares them, are `src/dllscan/convar_h.py`:
`ConVarRegList::Entry_t` is `ConVarCreation_t` (`CVarCreationBase_t`, then
`ConVarValueInfo_t`) and the two refs; its three `CVValue_t` are `uint8[16]`,
so they sit unaligned. That layout fits tier0's registry
(`capture-approach.kb/icvar-hook.md`): for every convar `server` or `client`
declares once (1999 and 2226), the entry's type, min, max and version equal the
registry's, and so does its default unless it has none. `m_Version` is the
registry's int16 at `ConVarData+42`: 0 except on 10 `archive` convars (1 to 3).

The padding holds stale stack bytes (pointer fragments too). In all 30 convar
queues (6223 entries), a present value's bytes past its type's size are zero,
and an absent one (has-byte 0) is 16 zero bytes. has-default is 0 on exactly the
`reference` declarations (181); for those tier0's registry holds the type's
zero value, version -1, and the declared flags without `developmentonly
defensive` (`capture-approach.kb/icvar-hook.md`).

`m_eVarType` is the row index of tier0's type-traits table (`.data`, RVA
`0x398610`, 88-byte rows: name pointer, byte size, …), not s2sdk's enum, which
lacks `int8` and `uint8`. The rows' names and sizes, and how each type's
`CVValue_t` decodes, are `src/dllscan/values.py`; a `string` holds a
`CUtlString`, a heap `char*` whose null reads as `""` (`utlstring.h:303`). The
queues of 6860 use bool, uint8, uint16, int32, uint32, uint64, float32,
string, color and vector2-4; no queue declares int8, int16, int64, float64,
qangle or vectorws.

Past its base, the 64-byte command entry holds only pointers (the callback, code
or an interface object in writable data; the completion callback; the
`m_Command` ref) and their kind bits, which are partly stale stack bytes: the
base is the whole record.
