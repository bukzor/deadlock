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
  access indices 0.. yields all 2003, the queue's names exactly; commands via 44.
  The `ConVarData` layout is s2sdk's, but `EConVarType` has `int8`, `uint8`
  after `bool` (float32 is 9, string 11). 1991 of 2002 defaults match
  GameTracking's DumpSource2 dump; the 11 that differ read zero where upstream
  has a value, all named for engine2 or client (`host_timescale`, `violence_*`).

Those 11 are `server`'s `reference` declarations: their has-default byte is 0,
and for such a declaration tier0's registry holds the type's zero value and
version -1 (6860, `../registration-flow.md`, "The convar entry's layout").

The readback is built, without the vtable hook, as the registry readback check
(`dllscan registry`; `../validation.md`, "Registry readback"). On 6860 it
establishes, for `server` and `client`:

- **Both replay their whole queues** before `Init` stops (`server` at
  `IPulseSystem_001`, `client` at `RenderDevice003`): each registry holds
  exactly the queue's distinct names (2003 convars and 493 commands, 2234 and
  428), so none of tier0's own queue (3 convars, 24 commands): the cvar
  system's `Connect` doesn't register it. A walk ends where `GetConVarData`
  returns null, or where `GetConCommandData` returns what the invalid index
  0xFFFF does: a shared tier0 `<unknown>` record, which 6854's count of 494
  commands included.
- **Registration's flag rule.** A once-declared entry registers with its
  declared flags plus the per-DLL flag (`../registration-flow.md`); 4 and 76
  convars and 6 and 8 commands declare it already. A `reference` declaration
  (19 and 69) instead registers without `developmentonly defensive`, the
  flags s2sdk's `SanitiseConVarFlags` put on the declaration, and gets no
  per-DLL flag. Besides, one convar per DLL carries tier0's runtime bits
  `initial_setvalue performing_callbacks` after `Init`
  (`citadel_hero_release_vote_august_2025_debug_votes_cast_total`,
  `r_citadel_shadow_quality`).

> [!QUESTION] Why that one convar per DLL carries `initial_setvalue
> performing_callbacks`.

> [!QUESTION] Whether every other DLL with a queue replays before its `Init`
> stops; and whether tier0's `Init` registers tier0's own queue (`find`,
> `cvarlist`).
