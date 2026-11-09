# How a convar gets registered

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
`gamedll` (server) or `clientdll` (client).

Entry sizes on 6848 and 6851, measured from the queues: `ConVarRegList::Entry_t`
160 bytes, `ConCommandRegList::Entry_t` 64 (`capture-approach.kb/queue-shape-scan.md`).

## The convar entry's layout (6860)

s2sdk's `ConVarCreation_t` (`convar.h:630-733`) in `Entry_t`, values packed:
each `CVValue_t` is a `uint8[16]`, so they sit unaligned. Fitted against tier0's registry
(`capture-approach.kb/icvar-hook.md`): for every convar `server` or `client`
declares once (1999 and 2226), the entry's type, min, max and version equal the
registry's, and so does its default unless it has none.

| offset | size | field |
|---|---|---|
| 0 | 24 | `CVarCreationBase_t`: name, help, flags |
| 24 | 4 | `m_Version`, int32: 0 except on 10 `archive` convars (1 to 3); the registry's int16 at `ConVarData+42` |
| 28, 29, 30 | 1 each | has-default, has-min, has-max: 0 or 1 |
| 31, 47, 63 | 16 each | default, min, max `CVValue_t` |
| 80 | 40 | change-callback provider and callback, filter provider and filter, enum-info getter: code pointers |
| 120 | 2 | `m_eVarType`, int16 |
| 128 | 16 | `CompletionCallbackInfo_t`: pointer, `m_bIsInterface` at 136 |
| 144, 152 | 8 each | `m_pConVar`, `m_pConVarData` (the ref `reglist` owner-checks) |

Bytes 79, 122-127 and 137-143 are padding holding stale stack bytes (pointer
fragments too). In all 30 convar queues (6223 entries), a present value's bytes
past its type's size are zero, and an absent one (has-byte 0) is 16 zero bytes.
has-default is 0 on exactly the `reference` declarations (181); for those tier0's
registry holds the type's zero value and version -1.

`EConVarType` is the row index of tier0's type-traits table (`.data`, RVA
`0x398610`, 88-byte rows: name pointer, byte size, …), not s2sdk's enum, which
lacks `int8` and `uint8`:

| code | type | size | `CVValue_t` holds |
|---|---|---|---|
| 0 | bool | 1 | byte 0 or 1 |
| 1-8 | int8 uint8 int16 uint16 int32 uint32 int64 uint64 | 1 1 2 2 4 4 8 8 | little-endian integer |
| 9, 10 | float32 float64 | 4, 8 | IEEE float |
| 11 | string | 8 | `CUtlString`: a heap `char*`; null reads as `""` (`utlstring.h:303`) |
| 12 | color | 4 | r, g, b, a bytes |
| 13-17 | vector2 vector3 vector4 qangle vectorws | 8 12 16 12 12 | 2, 3, 4, 3, 3 float32 |

The queues of 6860 use bool, uint8, uint16, int32, uint32, uint64, float32,
string, color and vector2-4; no queue declares int8, int16, int64, float64,
qangle or vectorws.

The 64-byte command entry holds, past its base: the callback pointer (code, or
an interface object in writable data) at 24, kind bytes at 32 that are partly
stale stack bytes, the completion pointer at 40 and its `m_bIsInterface` at 48,
and the `m_Command` ref at 56. Only pointers and their kinds, so the base is the
whole record.
