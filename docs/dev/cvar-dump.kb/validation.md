# Checks that keep the dump honest

Any dumper that reads engine memory can read garbage after a patch. Trust comes
from checks that fail loudly, not from the dumper's author.

These fail the build on every run (non-zero exit, no output written):

- **Shape:** every DLL but tier0 has its queues located from its load's
  allocator log (`capture-approach.kb/allocator-hook.md`): exactly one of
  its writable qwords holds the newest block it allocated of a kind's size,
  the chain from there runs back over exactly the blocks it allocated,
  newest first, and every entry fits. The allocator's slot is read from
  `MemAlloc_AllocFunc`'s code, and a log that fills fails rather than
  truncates. tier0, whose queues predate any hook, has at most one queue
  of each kind by shape scan (`capture-approach.kb/queue-shape-scan.md`). An
  entry fits if its name pointer lands inside the DLL on a NUL-terminated
  printable string, its help pointer is null or inside the DLL, and its
  trailing ref passes its kind's test (a convar's lands in the DLL's
  writable sections; a command's reads as an unregistered `ConCommandRef`).
  Decoding a queue raises on any misfit: a type outside the binary's type
  table, a has-default / min / max byte other than 0 or 1, nonzero bytes
  past a value's size or in an absent value, a non-finite float, an
  unreadable string. In tier0's shape scan alone, an entry that misfits
  hides its queue instead of failing it; Coverage and the Oracle are the
  backstop.
- **Anchors:** names known by other means arrive in the right queue, with the
  right flags — `bot_kick_all` a command (run in-game), `citadel_bot_kick` a
  `developmentonly` command, `citadel_lane_swap_available_duration_prematch` a
  `replicated cheat` convar, `find` a tier0 command.
- **Coverage:** every DLL (`dll-coverage.md`) has a `load` record, and every
  `ok` one is scanned; `engine2`, `client` and `server` each yield both queues.
  This is also what fails if an entry's size moves: no block of the expected
  size is allocated, so those three yield none.

The targets under `data/dlls.check/` check the anchors and which DLLs yield
queues; every other check is an atom or an aggregate failing.

Run on demand, and on each new build, not as part of `all.do`:

- **Registry readback** (`redo data/dlls.check/registry`): for `server` and
  `client`, tier0's own registry after the DLL's `Init` replayed its queues
  (`capture-approach.kb/icvar-hook.md`; `dllscan registry`) holds every queue
  entry's name, and each name declared once as the queue declares it: type,
  default, min, max, version, help, and flags plus the per-DLL flag
  registration adds (`bukzor_deadlock.registry_check` states the rule, `reference`
  declarations included). Checks the value decoding against the engine, not
  against our reading of the SDK. `Init` must stop at a placeholder's trap or
  return; a fault no placeholder explains fails the readback
  (`bukzor_dllscan.registry.stopped_by`), since the registry could then hold a
  partial replay.
- **Oracle** (`redo data/dlls.check/cvarlist`): the engine's own `cvarlist`
  (`capture-approach.kb/runtime-cvarlist.md`), captured fresh on a dedicated
  server and on a client (`../game-runtime.kb/cvarlist-capture.md`), against
  the store. Every listed name is declared; every listable declaration
  (not `developmentonly` or `hidden`, not a `-` command) of a DLL the listing
  proves loaded is listed; and each listed name's flags, help and value are
  its declarations', through the listing's print rules, the value overridden
  by `gameinfo.gi` or the user (`differences`). `bukzor_deadlock.cvarlist_check`
  states each rule. The only check that catches a DLL whose queue the scan
  missed outright.
