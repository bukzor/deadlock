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

`EConVarType` in the binary has `int8`, `uint8` after `bool` (so float32 is 9,
string 11), unlike s2sdk's copy (6854, `capture-approach.kb/icvar-hook.md`).

Entry sizes on 6848 and 6851, measured from the queues: `ConVarRegList::Entry_t`
160 bytes, `ConCommandRegList::Entry_t` 64 (`capture-approach.kb/queue-shape-scan.md`).
