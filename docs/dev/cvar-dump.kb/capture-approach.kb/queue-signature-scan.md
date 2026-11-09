# Read each DLL's queue via a code signature (DumpSource2's way; fallback)

After loading a DLL, before `Connect`, find its inlined `AddToList` by byte
pattern and resolve the RIP-relative load in it to `s_pRoot`; walk the blocks.
Windows convar pattern (DumpSource2 `gamedata.h:216`):
`4C 8B 0D ?? ?? ?? ?? 4D 85 C9 74 ?? 45 8B 01 41 83 F8 64` — load head, test,
read `m_nSize`, compare to 100. Commands have a sibling pattern.

For: needs only `LoadLibrary`, not a working `Connect`, so a DLL whose `Connect`
fails still yields its convars. Proven: GameTracking dumps every build with it.

Against: a hand-maintained pattern per list kind that a recompile can break or,
worse, match the wrong code; DumpSource2 requires exactly one match per DLL to
catch the second case. Also needs the `Entry_t` layout, which the hook gets from
the call instead.

Superseded by `queue-shape-scan.md`, which reads the same queues without the
pattern and agreed with it on every head (6848). Its pattern stays useful as a
one-off cross-check when the shape scan fails.
