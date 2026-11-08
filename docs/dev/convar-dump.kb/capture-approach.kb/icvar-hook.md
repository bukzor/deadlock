# Hook ICvar's two registration methods (reopened: `Init` runs the replay)

Load `tier0.dll`, take the real cvar system (`VEngineCvar007`) from its
`CreateInterface`, `Connect` it, and give it a private vtable whose
`RegisterConVar`/`RegisterConCommand` record the creation struct before calling
the original. Then `Connect` and `Init` each DLL's app system through our own
factory and catch the queue replay.

Two pieces remove hard-coded slots and names:

- **Slot discovery by behaviour.** Every slot of the private vtable is a 44-byte
  x64 stub that logs `(slot, rdx, r8)` and tail-jumps to the original (scratch
  registers only, `jmp` not `call`, so unknown signatures pass through intact;
  encoding verified with capstone). The replay passes `&m_Entries[i].m_Info` in
  order, so the registration slot is the one whose argument advances by a
  constant stride; `rdx` for `RegisterConVar`, `r8` for `RegisterConCommand`
  (hidden return pointer).
- **Interface names from the DLL's own requests** to our factory.

Evidence, build 6851 (`../../probes/hook_probe2.py`, 2026-11-05), factory serving
tier0 only. Controls: a `GetTier` call through the hooked object is logged; the
DLL asks for `VEngineCvar007` and gets the hooked object; and, independent of the
hook, each queue entry's result slot (`*pCvarData`, `*m_Command`) is snapshotted
before and after.

| DLL | after `Connect` | after `Init` (access violation) |
|---|---|---|
| `server.dll` | 0 calls, 0 of 2007 + 493 slots written | slot 38 ×2007 (`rdx` stride 160), slot 42 ×493 (`r8` stride 64), every slot written |
| `client.dll` | 0 calls, 0 of 2288 + 427 | slot 38 ×2288, slot 42 ×427, every slot written |

So the replay is in `Init`. `server`'s `Init` then faults on its first use of
`IPulseSystem_001` (slot 52 through a null global, `server+0x27a8fec`; the
global is the one `Connect`'s name→global table pairs with that name), which a
tier0-only factory left unserved. The access violation surfaces as a Python
`OSError` and the process lives on; at exit the DLLs' static `ConVar`
destructors call `g_pCVar` again, so the original vtable must be restored first.
Slots 38 and 42 are where s2sdk's `icvar.h` declaration order puts
`RegisterConVar` and `RegisterConCommand`; the other slots called (11, 14, 16,
17, 23, 40, 41) are its `FindConVar`, change/filter callbacks, `FindConCommand`,
`LockConVarValueInitialisation` and `GetConVarData`.

The 6848 decline (`../../probes/convar_probe.py`) was an artifact: it read the
log only after `Init` returned, and `Init` raised, so the calls went unseen; its
other signal, an unchanged queue head, can't show a replay, since s2sdk's
`RegisterAll` leaves the blocks in place (`convar.cpp:161`).

For, over `./queue-shape-scan.md`: tier0 merges same-named declarations itself,
while the hook still sees which DLL made each call, so the merge rule
(`../output-views.md`) comes from the engine; and the registered values are
held by tier0, a possible way around decoding `ConVarValueInfo_t` ourselves.

Against: calls into each DLL's `Init` with most of the engine missing, which
crashes; a DLL whose `Init` faults before its replay yields nothing. Depends on
the `IAppSystem` slot order (`Connect` 0, `Init` 3).

Evidence, build 6854 (`../../probes/hook_probe3.py`, 2026-11-05), `server.dll`:

- **Placeholder factory.** Every name tier0 can't serve gets its own object
  whose stubs log and return 0 during `Connect`, and trap (`ud2`) during
  `Init`. `Connect` does use its dependencies when they're non-null
  (`IPulseSystem_001` slot 32, `SchemaSystem_001` 26,
  `ResourceManifestRegistry001` 0 and 2), so a placeholder that traps from the
  start stops inside `Connect`. With the two modes, `Connect` succeeds and
  `Init` registers 2008 convars and 493 commands, then stops at
  `IPulseSystem_001` slot 52.
- **Readback.** `FindFirstConVar`/`FindNextConVar` (12/13) skip hidden entries:
  785 of 2003, none `developmentonly`/`defensive`. `GetConVarData` (41) over
  access indices 0.. yields all 2003, the queue's names exactly; commands via 44,
  494 against the queue's 493. The `ConVarData` layout is s2sdk's, but
  `EConVarType` has `int8`, `uint8` after `bool` (float32 is 9, string 11).
  Registry flags are the queue's OR `gamedll` (0x4) for 1978; 20 gain
  `developmentonly|defensive` instead (s2sdk's `SanitiseConVarFlags`); 5 others
  unexplained. 1991 of 2002 defaults match GameTracking's DumpSource2 dump; the
  11 that differ read zero where upstream has a value, all named for engine2 or
  client (`host_timescale`, `violence_*`).

> [!QUESTION] Whether those 11 are `server`'s reference declarations, filled in
> when the owning DLL registers; whether every in-scope DLL replays before its
> `Init` stops; and whether tier0's own queue (`find`, `cvarlist`) needs tier0's
> `Init`.
