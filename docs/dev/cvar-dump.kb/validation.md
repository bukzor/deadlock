# Checks that keep the dump honest

Any dumper that reads engine memory can read garbage after a patch. Trust comes
from checks that fail loudly, not from the dumper's author.

These fail the build on every run (non-zero exit, no output written):

- **Shape:** `server.dll` yields exactly two multi-block strides, equal to the
  pinned ones (a check target of its own, `data/dlls.check/strides`,
  `capture-approach.kb/queue-shape-scan.md`); every DLL has at most one queue
  of each kind at those strides. A head is a queue only if every entry fits:
  its name pointer lands inside the DLL on a NUL-terminated printable string,
  its help pointer is null or inside the DLL, and its trailing ref passes its
  kind's test (a convar's lands in the DLL's writable sections; a command's
  reads as an unregistered `ConCommandRef`). Decoding a queue that fit raises
  on any misfit: a type outside the binary's type table, a has-default / min /
  max byte other than 0 or 1, nonzero bytes past a value's size or in an
  absent value, a non-finite float, an unreadable string. An entry that
  misfits hides its queue instead of failing it; Coverage and the Oracle are
  the backstop.
- **Anchors:** names known by other means arrive in the right queue, with the
  right flags — `bot_kick_all` a command (run in-game), `citadel_bot_kick` a
  `developmentonly` command, `citadel_lane_swap_available_duration_prematch` a
  `replicated cheat` convar, `find` a tier0 command. These also decide which
  stride is which.
- **Coverage:** every DLL (`dll-coverage.md`) has a `load` record, and every
  `ok` one is scanned; `engine2`, `client` and `server` each yield both queues.

The targets under `data/dlls.check/` check the strides, the anchors, and which
DLLs yield queues; every other check is an atom or an aggregate failing.

> [!TODO] Run on demand, not on every build:
>
> - **Oracle:** the non-`developmentonly` entries equal the engine's own
>   `cvarlist` (`capture-approach.kb/runtime-cvarlist.md`) for the same build,
>   on name, flags, and default. The only check that catches a DLL whose queue
>   the scan missed outright. Too slow for every build, run on demand.
> - **Registry readback:** for `server` and `client`, every queue entry is a
>   registration call, and each name declared once decodes, from the queue, to
>   the type, flags (minus the per-DLL flag) and default tier0's own registry
>   holds (`capture-approach.kb/icvar-hook.md`; `../probes/hook_probe3.py` does
>   the readback). Checks the value decoding against the engine, not against
>   our reading of the SDK. Run on demand, and on each new build.
